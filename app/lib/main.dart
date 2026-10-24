import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_tts/flutter_tts.dart';
import 'package:path/path.dart' as p;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite/sqflite.dart';

// ---------- Theme (Light / Dark / Follow system) ----------

/// Current theme mode, shared by every page. Persisted in SharedPreferences
/// so the choice survives app restarts.
final ValueNotifier<ThemeMode> themeModeNotifier =
    ValueNotifier<ThemeMode>(ThemeMode.system);

const _themePrefKey = 'theme_mode';

Future<void> _loadThemeMode() async {
  final prefs = await SharedPreferences.getInstance();
  final saved = prefs.getString(_themePrefKey);
  themeModeNotifier.value = switch (saved) {
    'light' => ThemeMode.light,
    'dark' => ThemeMode.dark,
    _ => ThemeMode.system,
  };
}

/// Cycles System -> Light -> Dark -> System, and saves the choice.
Future<void> cycleThemeMode() async {
  themeModeNotifier.value = switch (themeModeNotifier.value) {
    ThemeMode.system => ThemeMode.light,
    ThemeMode.light => ThemeMode.dark,
    ThemeMode.dark => ThemeMode.system,
  };
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString(
    _themePrefKey,
    switch (themeModeNotifier.value) {
      ThemeMode.light => 'light',
      ThemeMode.dark => 'dark',
      ThemeMode.system => 'system',
    },
  );
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await _loadThemeMode();
  runApp(const KamusApp());
}

// ---------- Model ----------

class WordEntry {
  final int id;
  final String word;
  final String? pos;
  final String? definitionEn;
  final String? example;
  final String? ipaUs;
  final String? ipaUk;
  final String? ipaOther;
  final String? glossId;
  final String? synonyms;
  final String? antonyms;
  final String? syllables;
  final int? syllableCount;
  final int? stressIndex;
  final int? freqRank;

  const WordEntry({
    required this.id,
    required this.word,
    this.pos,
    this.definitionEn,
    this.example,
    this.ipaUs,
    this.ipaUk,
    this.ipaOther,
    this.glossId,
    this.synonyms,
    this.antonyms,
    this.syllables,
    this.syllableCount,
    this.stressIndex,
    this.freqRank,
  });

  factory WordEntry.fromMap(Map<String, Object?> m) => WordEntry(
        id: m['id'] as int,
        word: m['word'] as String,
        pos: m['pos'] as String?,
        definitionEn: m['definition_en'] as String?,
        example: m['example'] as String?,
        ipaUs: m['ipa_us'] as String?,
        ipaUk: m['ipa_uk'] as String?,
        ipaOther: m['ipa_other'] as String?,
        glossId: m['gloss_id'] as String?,
        synonyms: m['synonyms'] as String?,
        antonyms: m['antonyms'] as String?,
        syllables: m['syllables'] as String?,
        syllableCount: m['syllable_count'] as int?,
        stressIndex: m['stress_index'] as int?,
        freqRank: m['freq_rank'] as int?,
      );
}

// ---------- Database ----------

class KamusDb {
  static Database? _db;

  static Future<Database> instance() async {
    if (_db != null) return _db!;
    final dbDir = await getDatabasesPath();
    // Versioned filename so a future dataset update is not shadowed by a stale copy.
    final path = p.join(dbDir, 'kamus_v24.sqlite');
    if (!await File(path).exists()) {
      final data = await rootBundle.load('assets/kamus_v24.sqlite');
      final bytes =
          data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);
      await File(path).writeAsBytes(bytes, flush: true);
    }
    _db = await openDatabase(path, readOnly: true);
    return _db!;
  }

  static Future<List<WordEntry>> search(String query) async {
    final db = await instance();
    final q = query.trim().toLowerCase();
    final List<Map<String, Object?>> rows;
    if (q.isEmpty) {
      rows = await db.query('words',
          orderBy: '(freq_rank IS NULL) ASC, freq_rank ASC, word ASC',
          limit: 100);
    } else {
      rows = await db.rawQuery(
        'SELECT * FROM words WHERE word LIKE ? '
        'ORDER BY (LOWER(word) = ?) DESC, (word LIKE ?) DESC, '
        '(freq_rank IS NULL) ASC, freq_rank ASC, word ASC LIMIT 100',
        ['%$q%', q, '$q%'],
      );
    }
    return rows.map(WordEntry.fromMap).toList();
  }

  static Future<WordEntry?> lookup(String word) async {
    final db = await instance();
    final rows = await db.query('words',
        where: 'word = ?', whereArgs: [word.toLowerCase()], limit: 1);
    if (rows.isEmpty) return null;
    return WordEntry.fromMap(rows.first);
  }
}

// ---------- TTS ----------

class Speaker {
  static final FlutterTts _tts = FlutterTts();
  static bool _ready = false;

  static Future<void> _init() async {
    if (_ready) return;
    await _tts.setLanguage('en-GB');
    await _tts.setPitch(1.0);
    _ready = true;
  }

  static Future<void> speak(String text, {required double rate}) async {
    await _init();
    await _tts.stop();
    await _tts.setSpeechRate(rate);
    await _tts.speak(text);
  }

  static Future<void> stop() async {
    await _tts.stop();
  }
}

// ---------- App ----------

class KamusApp extends StatelessWidget {
  const KamusApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: themeModeNotifier,
      builder: (context, mode, _) {
        return MaterialApp(
          title: 'English Dictionary: Pronounce It!',
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
            useMaterial3: true,
          ),
          darkTheme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: Colors.indigo,
              brightness: Brightness.dark,
            ),
            useMaterial3: true,
          ),
          themeMode: mode,
          home: const HomePage(),
        );
      },
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();
  Future<List<WordEntry>> _results = KamusDb.search('');

  @override
  void initState() {
    super.initState();
    // autofocus:true alone is unreliable on first launch (window not yet
    // focused when the field is built), so request focus after the first
    // frame is drawn — plus one delayed retry, because some OEM keyboards
    // drop a show request that arrives during the launch transition.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _focusNode.requestFocus();
    });
    Future.delayed(const Duration(milliseconds: 450), () {
      if (mounted && !_focusNode.hasFocus) _focusNode.requestFocus();
    });
  }

  void _onSearch(String value) {
    setState(() {
      _results = KamusDb.search(value);
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pronounce It!',
            style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          ValueListenableBuilder<ThemeMode>(
            valueListenable: themeModeNotifier,
            builder: (context, mode, _) {
              final (icon, tip) = switch (mode) {
                ThemeMode.light => (Icons.light_mode, 'Theme: Light'),
                ThemeMode.dark => (Icons.dark_mode, 'Theme: Dark'),
                ThemeMode.system =>
                  (Icons.brightness_auto, 'Theme: Follow system'),
              };
              return IconButton(
                icon: Icon(icon),
                tooltip: tip,
                onPressed: cycleThemeMode,
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.info_outline),
            tooltip: 'About',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const AboutPage()),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _controller,
              focusNode: _focusNode,
              autofocus: true,
              onChanged: _onSearch,
              decoration: InputDecoration(
                hintText: 'Search a word…',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _controller.text.isEmpty
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.clear),
                        tooltip: 'Clear',
                        onPressed: () {
                          _controller.clear();
                          _onSearch('');
                          _focusNode.requestFocus();
                        },
                      ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ),
          Expanded(
            child: FutureBuilder<List<WordEntry>>(
              future: _results,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return Center(child: Text('Error: ${snapshot.error}'));
                }
                final words = snapshot.data ?? [];
                if (words.isEmpty) {
                  return const Center(child: Text('No words found.'));
                }
                return ListView.separated(
                  itemCount: words.length,
                  separatorBuilder: (context, index) =>
                      const Divider(height: 1),
                  itemBuilder: (context, i) {
                    final w = words[i];
                    final ipa = w.ipaUk ?? w.ipaOther ?? w.ipaUs;
                    return ListTile(
                      title: Text(w.word,
                          style: const TextStyle(
                              fontSize: 18, fontWeight: FontWeight.w600)),
                      subtitle: Text(
                        [
                          if (w.pos != null) w.pos!,
                          if (ipa != null) '/$ipa/',
                        ].join('  ·  '),
                      ),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => DetailPage(entry: w),
                          ),
                        ).then((_) {
                          // Back from a word: keyboard up, ready to search.
                          WidgetsBinding.instance.addPostFrameCallback((_) {
                            if (mounted) _focusNode.requestFocus();
                          });
                        });
                      },
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

// ---------- Detail ----------

class DetailPage extends StatefulWidget {
  final WordEntry entry;
  const DetailPage({super.key, required this.entry});

  @override
  State<DetailPage> createState() => _DetailPageState();
}

class _DetailPageState extends State<DetailPage> {
  WordEntry get w => widget.entry;

  @override
  void dispose() {
    Speaker.stop();
    super.dispose();
  }

  Widget _syllableLine() {
    final raw = w.syllables;
    if (raw == null || raw.isEmpty) return const SizedBox.shrink();
    final parts = raw.split('·');
    final stressIdx = (w.stressIndex ?? 0) - 1; // stored 1-based
    return RichText(
      text: TextSpan(
        // No explicit color: inherits the theme's default text color,
        // so syllables stay readable in both light and dark mode.
        style: const TextStyle(fontSize: 20),
        children: [
          for (var i = 0; i < parts.length; i++) ...[
            if (i > 0) const TextSpan(text: ' · '),
            TextSpan(
              text: parts[i],
              style: TextStyle(
                fontWeight:
                    i == stressIdx ? FontWeight.bold : FontWeight.normal,
                color: i == stressIdx
                    ? Theme.of(context).colorScheme.primary
                    : null,
              ),
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      appBar: AppBar(title: Text(w.word)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(w.word,
                style:
                    const TextStyle(fontSize: 36, fontWeight: FontWeight.bold)),
            if (w.pos != null)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(w.pos!,
                    style: const TextStyle(
                        fontSize: 16, fontStyle: FontStyle.italic)),
              ),
            const SizedBox(height: 16),
            Builder(builder: (context) {
              // One primary pronunciation only, UK first:
              // UK -> untagged Wiktionary -> US (last resort). No mixing.
              final primary = w.ipaUk ?? w.ipaOther ?? w.ipaUs;
              if (primary == null) return const SizedBox.shrink();
              final label = w.ipaUk != null
                  ? 'IPA (UK)'
                  : (w.ipaOther != null ? 'IPA' : 'IPA (US)');
              return Text('$label:  /$primary/',
                  style: const TextStyle(
                      fontSize: 19, fontWeight: FontWeight.w600));
            }),
            const SizedBox(height: 8),
            _syllableLine(),
            if (w.syllableCount != null)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text('${w.syllableCount} syllable(s)',
                    style: const TextStyle(color: Colors.grey)),
              ),
            const SizedBox(height: 20),
            Row(
              children: [
                FilledButton.icon(
                  onPressed: () => Speaker.speak(w.word, rate: 0.5),
                  icon: const Icon(Icons.volume_up),
                  label: const Text('Listen'),
                ),
                const SizedBox(width: 8),
                OutlinedButton.icon(
                  onPressed: () => Speaker.speak(w.word, rate: 0.25),
                  icon: const Icon(Icons.slow_motion_video),
                  label: const Text('Slow'),
                ),
              ],
            ),
            const SizedBox(height: 24),
            if (w.glossId != null && w.glossId!.isNotEmpty) ...[
              const Text('Arti (Bahasa Indonesia)',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text(w.glossId!,
                  style: const TextStyle(fontSize: 16, height: 1.4)),
              const SizedBox(height: 20),
            ],
            const Text('Definition',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(w.definitionEn ?? '-',
                style: const TextStyle(fontSize: 16, height: 1.4)),
            if (w.example != null && w.example!.isNotEmpty) ...[
              const SizedBox(height: 20),
              const Text('Example',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text(w.example!,
                  style: const TextStyle(
                      fontSize: 16,
                      height: 1.4,
                      fontStyle: FontStyle.italic)),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: () => Speaker.speak(w.example!, rate: 0.5),
                icon: const Icon(Icons.volume_up),
                label: const Text('Listen to example'),
              ),
            ],
            if (w.synonyms != null && w.synonyms!.isNotEmpty) ...[
              const SizedBox(height: 24),
              Text('Synonyms',
                  style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: dark
                          ? Colors.green.shade300
                          : Colors.green.shade800)),
              const SizedBox(height: 8),
              _wordChips(
                context,
                w.synonyms!.split(', '),
                background:
                    dark ? Colors.green.shade900 : Colors.green.shade50,
                border:
                    dark ? Colors.green.shade700 : Colors.green.shade300,
                foreground:
                    dark ? Colors.green.shade100 : Colors.green.shade900,
              ),
            ],
            if (w.antonyms != null && w.antonyms!.isNotEmpty) ...[
              const SizedBox(height: 20),
              Text('Antonyms',
                  style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: dark ? Colors.red.shade300 : Colors.red.shade800)),
              const SizedBox(height: 8),
              _wordChips(
                context,
                w.antonyms!.split(', '),
                background: dark ? Colors.red.shade900 : Colors.red.shade50,
                border: dark ? Colors.red.shade700 : Colors.red.shade300,
                foreground: dark ? Colors.red.shade100 : Colors.red.shade900,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// Tappable word chips (synonyms / antonyms): tap jumps to that word's page.
Widget _wordChips(
  BuildContext context,
  List<String> words, {
  required Color background,
  required Color border,
  required Color foreground,
}) {
  return Wrap(
    spacing: 8,
    runSpacing: 8,
    children: [
      for (final word in words)
        InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () async {
            final entry = await KamusDb.lookup(word);
            if (entry != null && context.mounted) {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => DetailPage(entry: entry),
                ),
              );
            }
          },
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: background,
              border: Border.all(color: border),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(word,
                style: TextStyle(fontSize: 15, color: foreground)),
          ),
        ),
    ],
  );
}

// ---------- About ----------

class AboutPage extends StatelessWidget {
  const AboutPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('About')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('English Dictionary: Pronounce It!',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('Version 1.4.0 - beta · October 2026',
                style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 24),
            const Text(
              'Proudly presented for the Four Pillars English Club '
              'of Panca Bhakti Vocational High School',
              style: TextStyle(
                  fontSize: 16,
                  height: 1.45,
                  fontWeight: FontWeight.bold,
                  fontStyle: FontStyle.italic),
            ),
            const SizedBox(height: 24),
            const Text('Data sources (all open)',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text(
              'Pronunciations: English Wiktionary via Kaikki '
              '(wiktextract), CC BY-SA. Indonesian meanings: English '
              'Wiktionary translations (CC BY-SA) & WordNet Bahasa '
              '(MIT). Definitions, synonyms & antonyms: Open English '
              'WordNet (via NLTK) & English Wiktionary (CC BY-SA). '
              'Syllables & stress: CMU Pronouncing Dictionary. '
              'Frequency ranking: wordfreq.',
              style: TextStyle(fontSize: 14, height: 1.45),
            ),
            const SizedBox(height: 32),
            const Text('Developed by',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('Muhammad Abdul Aziz, S.Pd',
                style: TextStyle(fontSize: 16)),
          ],
        ),
      ),
    );
  }
}
