import 'package:flutter_test/flutter_test.dart';
import 'package:kamus_pronunciation/main.dart';

void main() {
  test('WordEntry.fromMap maps dataset columns', () {
    final entry = WordEntry.fromMap({
      'id': 1,
      'word': 'education',
      'pos': 'noun',
      'definition_en': 'the activities of educating or instructing',
      'example': 'he received no formal education',
      'ipa_us': 'ˌɛdʒəˈkeɪʃən',
      'ipa_uk': null,
      'syllables': 'ɛ·dʒə·keɪ·ʃən',
      'syllable_count': 4,
      'stress_index': 3,
      'freq_rank': 526,
      'gloss_id': null,
    });
    expect(entry.word, 'education');
    expect(entry.syllableCount, 4);
    expect(entry.stressIndex, 3);
    expect(entry.ipaUk, isNull);
  });
}
