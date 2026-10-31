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
  final String? posAll;
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
  final VerbForms? verbForms;

  const WordEntry({
    required this.id,
    required this.word,
    this.pos,
    this.posAll,
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
    this.verbForms,
  });

  /// All parts of speech, e.g. "verb · noun · adjective".
  /// Falls back to the single legacy pos when pos_all is absent.
  String get posLabel {
    final raw = (posAll?.isNotEmpty == true ? posAll : pos) ?? '';
    return raw.split(',').where((s) => s.isNotEmpty).join(' · ');
  }

  WordEntry copyWith({String? posAll, VerbForms? verbForms}) => WordEntry(
        id: id,
        word: word,
        pos: pos,
        posAll: posAll ?? this.posAll,
        definitionEn: definitionEn,
        example: example,
        ipaUs: ipaUs,
        ipaUk: ipaUk,
        ipaOther: ipaOther,
        glossId: glossId,
        synonyms: synonyms,
        antonyms: antonyms,
        syllables: syllables,
        syllableCount: syllableCount,
        stressIndex: stressIndex,
        freqRank: freqRank,
        verbForms: verbForms ?? this.verbForms,
      );

  factory WordEntry.fromMap(Map<String, Object?> m) => WordEntry(
        id: m['id'] as int,
        word: m['word'] as String,
        pos: m['pos'] as String?,
        posAll: m['pos_all'] as String?,
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

// ---------- Verb principal parts (v1 / v2 past / v3 past participle) ----------

class VerbForms {
  final String v1;
  final List<String> v2;
  final List<String> v3;
  final String kind; // 'base', 'v2', 'v3'
  final bool regular;
  final Map<String, bool> links; // form -> exists in DB
  const VerbForms({
    required this.v1,
    required this.v2,
    required this.v3,
    required this.kind,
    required this.regular,
    required this.links,
  });
}

class _Scored {
  final int rank;
  final int freq;
  final WordEntry entry;
  _Scored(this.rank, this.freq, this.entry);
}

// ---------- Database ----------

// Irregular verbs: "base v2 v3" per line (UK forms). Parsed once.
const _irregularTxt = '''
arise arose arisen
awake awoke awoken
be was/were been
bear bore born
beat beat beaten
become became become
begin began begun
bend bent bent
bet bet bet
bid bid bid
bind bound bound
bite bit bitten
bleed bled bled
blow blew blown
break broke broken
breed bred bred
bring brought brought
build built built
burn burnt burnt
burst burst burst
buy bought bought
cast cast cast
catch caught caught
choose chose chosen
cling clung clung
come came come
cost cost cost
creep crept crept
cut cut cut
deal dealt dealt
dig dug dug
do did done
draw drew drawn
dream dreamt dreamt
drink drank drunk
drive drove driven
eat ate eaten
fall fell fallen
feed fed fed
feel felt felt
fight fought fought
find found found
fit fit fit
flee fled fled
fling flung flung
fly flew flown
forbid forbade forbidden
forget forgot forgotten
forgive forgave forgiven
freeze froze frozen
get got got
give gave given
go went gone
grind ground ground
grow grew grown
hang hung hung
have had had
hear heard heard
hide hid hidden
hit hit hit
hold held held
hurt hurt hurt
keep kept kept
kneel knelt knelt
know knew known
lay laid laid
lead led led
lean leant leant
learn learnt learnt
leave left left
lend lent lent
let let let
lie lay lain
light lit lit
lose lost lost
make made made
mean meant meant
meet met met
pay paid paid
put put put
quit quit quit
read read read
ride rode ridden
ring rang rung
rise rose risen
run ran run
say said said
see saw seen
seek sought sought
sell sold sold
send sent sent
set set set
sew sewed sewn
shake shook shaken
shine shone shone
shoot shot shot
show showed shown
shrink shrank shrunk
shut shut shut
sing sang sung
sink sank sunk
sit sat sat
sleep slept slept
slide slid slid
smell smelt smelt
sow sowed sown
speak spoke spoken
speed sped sped
spell spelt spelt
spend spent spent
spill spilt spilt
spin spun spun
split split split
spoil spoilt spoilt
spread spread spread
spring sprang sprung
stand stood stood
steal stole stolen
stick stuck stuck
sting stung stung
stink stank stunk
strike struck struck
swear swore sworn
sweep swept swept
swim swam swum
swing swung swung
take took taken
teach taught taught
tear tore torn
tell told told
think thought thought
throw threw thrown
thrust thrust thrust
understand understood understood
wake woke woken
wear wore worn
weep wept wept
win won won
wind wound wound
withdraw withdrew withdrawn
wring wrung wrung
write wrote written
''';

class _Irreg {
  static final Map<String, List<List<String>>> base2forms = {};
  static final Map<String, List<String>> form2base = {};
  static bool _done = false;

  static void ensure() {
    if (_done) return;
    _done = true;
    for (final line in _irregularTxt.trim().split('\n')) {
      final p = line.trim().split(RegExp(r'\s+'));
      if (p.length != 3) continue;
      final v2s = p[1].split('/');
      final v3s = p[2].split('/');
      base2forms[p[0]] = [v2s, v3s];
      for (final v in v2s) {
        form2base.putIfAbsent(v, () => [p[0], 'v2']);
      }
      for (final v in v3s) {
        form2base.putIfAbsent(v, () => [p[0], 'v3']);
      }
    }
  }
}

class KamusDb {
  static Database? _db;

  static Future<Database> instance() async {
    if (_db != null) return _db!;
    final dbDir = await getDatabasesPath();
    // Versioned filename so a future dataset update is not shadowed by a stale copy.
    final path = p.join(dbDir, 'kamus_v28.sqlite');
    if (!await File(path).exists()) {
      final data = await rootBundle.load('assets/kamus_v28.sqlite');
      final bytes =
          data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);
      await File(path).writeAsBytes(bytes, flush: true);
    }
    _db = await openDatabase(path, readOnly: true);
    return _db!;
  }

  static String _escapeLike(String s) => s
      .replaceAll('\\', '\\\\')
      .replaceAll('%', '\\%')
      .replaceAll('_', '\\_');

  static Future<List<WordEntry>> search(String query) async {
    final db = await instance();
    final q = query.trim().toLowerCase();
    if (q.isEmpty) {
      final rows = await db.query('words',
          orderBy: '(freq_rank IS NULL) ASC, freq_rank ASC, word ASC',
          limit: 100);
      return rows.map(WordEntry.fromMap).toList();
    }
    final e = _escapeLike(q);
    final rows = await db.rawQuery(
      "SELECT * FROM words WHERE word LIKE ? ESCAPE '\\' "
      "ORDER BY (LOWER(word) = ?) DESC, (word LIKE ? ESCAPE '\\') DESC, "
      '(freq_rank IS NULL) ASC, freq_rank ASC, word ASC LIMIT 100',
      ['%$e%', q, '$e%'],
    );
    final results = rows.map(WordEntry.fromMap).toList();
    // Typo tolerance: single-typo variants when the direct search is thin.
    if (results.length < 10 &&
        q.length >= 3 &&
        q.length <= 20 &&
        !q.contains(' ')) {
      final have = results.map((w) => w.word).toSet();
      results.addAll(await _fuzzySearch(db, q, have, 100 - results.length));
    }
    // Damaged prefix: the query is the mistyped start of a longer word
    // (e.g. "aproxima" -> "approximately").
    if (results.length < 5 &&
        q.length >= 4 &&
        q.length <= 20 &&
        !q.contains(' ')) {
      final have = results.map((w) => w.word).toSet();
      results.addAll(await _prefixTypoSearch(db, q, have, 100 - results.length));
    }
    return results.take(100).toList();
  }

  static Future<List<WordEntry>> _fuzzySearch(
      Database db, String q, Set<String> have, int limit) async {
    final n = q.length;
    final found = <_Scored>[];
    Future<void> add(int rank, List<Map<String, Object?>> rows) async {
      for (final r in rows) {
        final w = WordEntry.fromMap(r);
        if (have.add(w.word)) {
          found.add(_Scored(rank, w.freqRank ?? 1000000000, w));
        }
      }
    }
    // Exact lookups: transposed adjacent letters, one extra letter.
    final exactVars = <String>{};
    for (var i = 0; i < n - 1; i++) {
      final v = q.substring(0, i) + q[i + 1] + q[i] + q.substring(i + 2);
      if (v != q) exactVars.add(v);
    }
    for (var i = 0; i < n; i++) {
      exactVars.add(q.substring(0, i) + q.substring(i + 1));
    }
    for (final v in exactVars) {
      await add(30, await db
          .rawQuery('SELECT * FROM words WHERE word = ? LIMIT 3', [v]));
    }
    // One wrong letter.
    for (var i = 0; i < n; i++) {
      final pat =
          '${_escapeLike(q.substring(0, i))}_${_escapeLike(q.substring(i + 1))}';
      await add(
          40,
          await db.rawQuery(
              "SELECT * FROM words WHERE word LIKE ? ESCAPE '\\' "
              'AND LENGTH(word) = ? LIMIT 5',
              [pat, n]));
    }
    // One missing letter.
    for (var i = 1; i <= n; i++) {
      final pat =
          '${_escapeLike(q.substring(0, i))}%${_escapeLike(q.substring(i))}';
      await add(
          32,
          await db.rawQuery(
              "SELECT * FROM words WHERE word LIKE ? ESCAPE '\\' "
              'AND LENGTH(word) = ? LIMIT 5',
              [pat, n + 1]));
    }
    found.sort((a, b) {
      final c = a.rank.compareTo(b.rank);
      return c != 0 ? c : a.freq.compareTo(b.freq);
    });
    return found.take(limit).map((s) => s.entry).toList();
  }

  static Future<List<WordEntry>> _prefixTypoSearch(
      Database db, String q, Set<String> have, int limit) async {
    final n = q.length;
    final found = <_Scored>[];
    for (var i = 1; i < n; i++) {
      final pat =
          '${_escapeLike(q.substring(0, i))}%${_escapeLike(q.substring(i))}%';
      final rows = await db.rawQuery(
          "SELECT * FROM words WHERE word LIKE ? ESCAPE '\\' "
          'AND LENGTH(word) BETWEEN ? AND ? LIMIT 4',
          [pat, n + 1, n + 6]);
      for (final r in rows) {
        final w = WordEntry.fromMap(r);
        if (have.add(w.word)) {
          found.add(_Scored(-i, w.freqRank ?? 1000000000, w));
        }
      }
    }
    found.sort((a, b) {
      final c = a.rank.compareTo(b.rank);
      return c != 0 ? c : a.freq.compareTo(b.freq);
    });
    return found.take(limit).map((s) => s.entry).toList();
  }

  static Future<WordEntry?> lookup(String word) async {
    final db = await instance();
    final rows = await db.query('words',
        where: 'word = ?', whereArgs: [word.toLowerCase()], limit: 1);
    if (rows.isEmpty) return null;
    var entry = WordEntry.fromMap(rows.first);
    // Known verb inflections (went, gone, ...) always list verb first.
    _Irreg.ensure();
    final pa = entry.posAll ?? '';
    if (_Irreg.form2base.containsKey(entry.word) &&
        !pa.split(',').contains('verb')) {
      entry = entry.copyWith(posAll: pa.isEmpty ? 'verb' : 'verb,$pa');
    }
    final vf = await verbForms(entry.word, entry.pos);
    if (vf != null) entry = entry.copyWith(verbForms: vf);
    return entry;
  }

  static Future<bool> _exists(String w) async {
    final db = await instance();
    final r = await db
        .rawQuery('SELECT 1 FROM words WHERE word = ? LIMIT 1', [w]);
    return r.isNotEmpty;
  }

  static List<String> _regularPastCandidates(String base) {
    final b = base.toLowerCase();
    if (b.endsWith('e')) return ['${b}d'];
    if (b.endsWith('c')) return ['${b}ked'];
    if (b.length > 2 &&
        b.endsWith('y') &&
        !'aeiouy'.contains(b[b.length - 2])) {
      return ['${b.substring(0, b.length - 1)}ied'];
    }
    final cands = ['${b}ed'];
    if (b.length >= 3 &&
        !'aeiouwxy'.contains(b[b.length - 1]) &&
        'aeiou'.contains(b[b.length - 2]) &&
        !'aeiou'.contains(b[b.length - 3])) {
      cands.add('$b${b[b.length - 1]}ed');
    }
    return cands;
  }

  static List<String> _regularBaseCandidates(String w) {
    final cands = <String>[];
    if (w.endsWith('ied') && w.length > 4) {
      cands.add('${w.substring(0, w.length - 3)}y');
    }
    if (w.endsWith('ed') && w.length > 3) {
      final stem = w.substring(0, w.length - 2);
      if (stem.length >= 2 &&
          stem[stem.length - 1] == stem[stem.length - 2] &&
          !'aeiou'.contains(stem[stem.length - 1])) {
        cands.add(stem.substring(0, stem.length - 1));
      }
      cands.add(stem);
      cands.add('${stem}e');
    }
    return cands;
  }

  static Future<VerbForms?> verbForms(String word, String? pos) async {
    _Irreg.ensure();
    final w = word.toLowerCase();
    Future<Map<String, bool>> linksOf(List<String> forms) async {
      final m = <String, bool>{};
      for (final f in forms) {
        m[f] = await _exists(f);
      }
      return m;
    }
    if (_Irreg.base2forms.containsKey(w)) {
      final v2s = _Irreg.base2forms[w]![0];
      final v3s = _Irreg.base2forms[w]![1];
      return VerbForms(
          v1: w,
          v2: v2s,
          v3: v3s,
          kind: 'base',
          regular: false,
          links: await linksOf([w, ...v2s, ...v3s]));
    }
    if (_Irreg.form2base.containsKey(w)) {
      final base = _Irreg.form2base[w]![0];
      final kind = _Irreg.form2base[w]![1];
      final v2s = _Irreg.base2forms[base]![0];
      final v3s = _Irreg.base2forms[base]![1];
      return VerbForms(
          v1: base,
          v2: v2s,
          v3: v3s,
          kind: kind,
          regular: false,
          links: await linksOf([base, ...v2s, ...v3s]));
    }
    String? v2;
    if (pos == 'verb') {
      for (final c in _regularPastCandidates(w)) {
        if (await _exists(c)) {
          v2 = c;
          break;
        }
      }
      v2 ??= _regularPastCandidates(w)[0];
    } else {
      for (final c in _regularPastCandidates(w)) {
        if (await _exists(c)) {
          v2 = c;
          break;
        }
      }
    }
    if (v2 != null) {
      return VerbForms(v1: w, v2: [v2], v3: [v2], kind: 'base', regular: true,
          links: {w: true, v2: await _exists(v2)});
    }
    if (w.endsWith('ed')) {
      final db = await instance();
      for (final b in _regularBaseCandidates(w)) {
        if (_Irreg.base2forms.containsKey(b)) continue;
        final r =
            await db.rawQuery('SELECT pos FROM words WHERE word = ?', [b]);
        if (r.isNotEmpty &&
            r.first['pos'] == 'verb' &&
            _regularPastCandidates(b)[0] == w) {
          final cands = _regularPastCandidates(b);
          var v2ok = cands[0];
          for (final c in cands) {
            if (await _exists(c)) {
              v2ok = c;
              break;
            }
          }
          return VerbForms(v1: b, v2: [v2ok], v3: [v2ok], kind: 'v2',
              regular: true, links: {b: true, v2ok: await _exists(v2ok)});
        }
      }
    }
    return null;
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
                          if (w.posLabel.isNotEmpty) w.posLabel,
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
  late WordEntry w;

  @override
  void initState() {
    super.initState();
    w = widget.entry;
    // Search rows lack verbForms (and the verb-first pos boost); refresh
    // from lookup() so the detail page always shows complete data.
    KamusDb.lookup(w.word).then((fresh) {
      if (fresh != null && mounted) setState(() => w = fresh);
    });
  }

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

  Widget _verbFormsSection() {
    final vf = w.verbForms;
    if (vf == null) return const SizedBox.shrink();
    final scheme = Theme.of(context).colorScheme;

    Widget formCell(String label, List<String> forms) {
      return Expanded(
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
          decoration: BoxDecoration(
            border: Border.all(color: scheme.outlineVariant),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Column(
            children: [
              Text(label,
                  style:
                      const TextStyle(fontSize: 11, color: Colors.grey)),
              const SizedBox(height: 4),
              Wrap(
                alignment: WrapAlignment.center,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  for (var i = 0; i < forms.length; i++) ...[
                    if (i > 0)
                      const Text(' / ',
                          style: TextStyle(color: Colors.grey)),
                    if (vf.links[forms[i]] == true)
                      InkWell(
                        onTap: () async {
                          final entry =
                              await KamusDb.lookup(forms[i]);
                          if (entry != null && context.mounted) {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) =>
                                    DetailPage(entry: entry),
                              ),
                            );
                          }
                        },
                        child: Text(forms[i],
                            style: TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                                color: scheme.primary)),
                      )
                    else
                      Text(forms[i],
                          style: const TextStyle(fontSize: 17)),
                  ],
                ],
              ),
            ],
          ),
        ),
      );
    }

    Widget? note;
    if (vf.kind == 'v2') {
      note = _verbNote('"${w.word}" is the past tense (V2) of "${vf.v1}".',
          vf, scheme);
    } else if (vf.kind == 'v3') {
      note = _verbNote(
          '"${w.word}" is the past participle (V3) of "${vf.v1}".',
          vf,
          scheme);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        Text('Verb forms${vf.regular ? ' (regular)' : ''}',
            style:
                const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Row(
          children: [
            formCell('V1', [vf.v1]),
            const SizedBox(width: 8),
            formCell('V2 · past', vf.v2),
            const SizedBox(width: 8),
            formCell('V3 · participle', vf.v3),
          ],
        ),
        if (note != null) ...[
          const SizedBox(height: 8),
          note,
        ],
      ],
    );
  }

  Widget _verbNote(String text, VerbForms vf, ColorScheme scheme) {
    // Link the base form inside the note text.
    final parts = text.split('"${vf.v1}"');
    return RichText(
      text: TextSpan(
        style: const TextStyle(fontSize: 14, color: Colors.grey, height: 1.4),
        children: [
          TextSpan(text: parts[0]),
          WidgetSpan(
            alignment: PlaceholderAlignment.middle,
            child: InkWell(
              onTap: () async {
                final entry = await KamusDb.lookup(vf.v1);
                if (entry != null && context.mounted) {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) => DetailPage(entry: entry)),
                  );
                }
              },
              child: Text('"${vf.v1}"',
                  style: TextStyle(
                      fontSize: 14,
                      color: scheme.primary,
                      fontWeight: FontWeight.w600)),
            ),
          ),
          if (parts.length > 1) TextSpan(text: parts[1]),
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
            if (w.posLabel.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(w.posLabel,
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
            _verbFormsSection(),
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
            const Text('Version 1.7.1 - beta · October 2026',
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
