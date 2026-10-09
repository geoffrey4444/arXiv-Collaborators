import contextlib
import csv
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'arxiv-collaborators.py'
spec = importlib.util.spec_from_file_location('collaborators', SCRIPT)
app = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app
spec.loader.exec_module(app)


def paper(title='A collaboration paper', group='LIGO Scientific', count=100,
          source='arxiv', link='https://arxiv.org/abs/2401.00001v2',
          authors=None, **kwargs):
    return app.Paper(
        title=title, date=kwargs.pop('date', (2024, 1, 1)),
        link=link, source=source,
        authors=[app.Author('First Author')] if authors is None else authors,
        collaborations={group} if group else set(), author_count=count,
        **kwargs)


class CollaborationReviewTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'review.tsv'

    def apply(self, papers):
        with contextlib.redirect_stderr(io.StringIO()):
            return app.apply_collaboration_review(
                self.path, papers, app.read_collaboration_review(self.path))

    def rows(self):
        return app.read_collaboration_review(self.path)

    def save_rows(self, rows):
        with self.path.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=app.REVIEW_COLUMNS,
                                    delimiter='\t')
            writer.writeheader()
            writer.writerows(rows)

    def test_target_groups_and_counts(self):
        for group in ['LIGO Scientific', 'LSC', 'LVK',
                      'LIGO Scientific and Virgo Collaborations', 'LISA',
                      'LISA Consortium Waveform Working Group',
                      'Einstein Telescope', 'ET']:
            with self.subTest(group=group):
                self.assertTrue(app.likely_full_collaborations(
                    paper(group=group, count=50)))
                self.assertFalse(app.likely_full_collaborations(
                    paper(group=group, count=49)))
        for group in ['Cosmic Explorer', 'SXS Collaboration', 'Virgo', '']:
            with self.subTest(group=group):
                self.assertFalse(app.likely_full_collaborations(
                    paper(group=group, count=2000)))
        # Mentioning a detector in the title/affiliation is not membership.
        self.assertFalse(app.likely_full_collaborations(paper(
            title='LISA and Einstein Telescope prospects', group='',
            authors=[app.Author('Lisa Randall', ['LIGO Scientific'])])))

    def test_corporate_authors_and_first_individual(self):
        p = paper(group='', count=0, authors=[
            app.Author('LISA Consortium Waveform Working Group'),
            app.Author(':'),
            app.Author('Niayesh Afshordi')
        ] + [app.Author(f'Person Surname{i}') for i in range(60)])
        self.assertTrue(app.likely_full_collaborations(p))
        self.assertEqual(p.first_author, 'Niayesh Afshordi')
        self.assertEqual(p.author_count, 61)
        # A corporate-only list is not interpreted as a one-person paper.
        p = paper(group='', count=1,
                  authors=[app.Author('ET Collaboration')])
        self.assertTrue(app.likely_full_collaborations(p))
        self.assertEqual(p.first_author, '')

    def test_merge_preserves_links_and_does_not_inflate_count(self):
        a = paper(count=20, group='LISA',
                  authors=[app.Author('A. Author')])
        b = paper(count=20, source='ads', group='',
                  link='https://ui.adsabs.harvard.edu/abs/2024Test....1A',
                  authors=[app.Author('Alice Author')])
        c = paper(count=20, source='inspire', group='LISA Consortium',
                  link='https://inspirehep.net/literature/123')
        merged = app.merge_papers([b, c, a])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].author_count, 20)
        self.assertFalse(app.likely_full_collaborations(merged[0]))
        row = app.review_row(merged[0])
        self.assertEqual(list(row), app.REVIEW_COLUMNS)
        self.assertEqual(row['arxiv_url'], 'https://arxiv.org/abs/2401.00001')
        self.assertEqual(row['scix_url'],
                         'https://scixplorer.org/abs/2024Test....1A/abstract')
        self.assertEqual(row['inspirehep_url'],
                         'https://inspirehep.net/literature/123')
        self.assertEqual(row['first_author'], 'A. Author')
        self.assertIn('LISA Consortium', row['collaboration'])

    def test_append_only_preserves_n_and_matches_versions_and_titles(self):
        original = paper(title='Étude: a\nmultiline\ttitle')
        self.assertEqual(self.apply([original]), [])
        rows = self.rows()
        self.assertEqual(rows[0]['omit'], 'Y')
        self.assertEqual(rows[0]['title'], 'Étude: a multiline title')
        rows[0]['omit'] = 'N'
        rows[0]['arxiv_url'] = 'http://arxiv.org/abs/2401.00001v1'
        self.save_rows(rows)
        before = self.path.read_bytes()
        revised = paper(title='A changed title',
                        link='https://arxiv.org/abs/2401.00001v4')
        self.assertEqual(self.apply([revised]), [revised])
        self.assertEqual(self.path.read_bytes(), before)
        # An alternate source with no shared URL still matches the title.
        alternate = paper(title='Etude a multiline title', source='inspire',
                          link='https://inspirehep.net/literature/456')
        new = paper(title='New paper', link='https://arxiv.org/abs/2501.00002')
        self.assertEqual(self.apply([alternate, new]), [alternate])
        self.assertTrue(self.path.read_bytes().startswith(before))
        self.assertEqual([r['omit'] for r in self.rows()], ['N', 'Y'])
        self.apply([new, alternate])
        self.assertEqual(len(self.rows()), 2)

    def test_first_author_fallback_when_arxiv_lists_only_group(self):
        merged, = app.merge_papers([
            paper(authors=[app.Author('LISA Collaboration')]),
            paper(source='ads', link='https://ui.adsabs.harvard.edu/abs/test',
                  authors=[app.Author('A. Author')]),
            paper(source='inspire', link='https://inspirehep.net/literature/1',
                  authors=[app.Author('Alice Author')]),
        ])
        self.assertEqual(merged.first_author, 'Alice Author')

    def test_only_file_decisions_exclude_no_cosmic_explorer_override(self):
        cosmic = paper(title='Cosmic Explorer', group='Cosmic Explorer')
        self.assertEqual(self.apply([cosmic]), [cosmic])
        self.assertEqual(self.rows(), [])
        self.save_rows([app.review_row(cosmic)])
        # A user-supplied Y must be honored regardless of the collaboration.
        self.assertEqual(self.apply([cosmic]), [])
        rows = self.rows()
        rows[0]['omit'] = 'N'
        self.save_rows(rows)
        self.assertEqual(self.apply([cosmic]), [cosmic])

    def test_incomplete_metadata_and_ads_url_alias(self):
        p = paper(link='https://ui.adsabs.harvard.edu/abs/2024Test....1A',
                  source='ads')
        self.apply([p])
        rows = self.rows()
        self.assertEqual(rows[0]['arxiv_url'], '')
        self.assertEqual(rows[0]['inspirehep_url'], '')
        rows[0]['scix_url'] = p.link + '/abstract'
        self.save_rows(rows)
        before = self.path.read_bytes()
        self.apply([paper(title='Changed title', source='ads', link=p.link)])
        self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_file_never_modified_and_missing_newline_appended(self):
        self.path.write_text('wrong\theader\n', encoding='utf-8')
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'expected TSV columns'):
            self.apply([paper()])
        self.assertEqual(self.path.read_bytes(), before)
        row = app.review_row(paper())
        row['omit'] = 'maybe'
        self.save_rows([row])
        with self.assertRaisesRegex(ValueError, 'omit Y or N'):
            self.apply([paper()])
        row['omit'] = 'N'
        self.save_rows([row])
        self.path.write_bytes(self.path.read_bytes().rstrip(b'\r\n'))
        self.apply([paper(title='New', link='https://arxiv.org/abs/2502.00003')])
        self.assertEqual(len(self.rows()), 2)

    def test_conflicting_decisions_fail_before_appending(self):
        row = app.review_row(paper())
        self.save_rows([row, dict(row, omit='N')])
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'conflicting omit'):
            self.apply([paper()])
        self.assertEqual(self.path.read_bytes(), before)

    def test_output_uses_only_retained_papers_and_date_window(self):
        year = app.dt.now().year
        shared = app.Author('Shared Person', ['Old Institute'], source='arxiv')
        kept = paper(title='Small team', group='', count=2,
                     date=(year - 1, 3, 4), authors=[shared],
                     link='https://arxiv.org/abs/2503.00001')
        skipped = paper(date=(year, 4, 5), authors=[
            app.Author('Shared Person', ['New Institute'], source='arxiv'),
            app.Author('Excluded Person')])
        old = paper(title='Old paper', date=(year - 5, 1, 1),
                    link='https://arxiv.org/abs/1901.00001')

        def run(review):
            output = io.StringIO()
            with patch.object(app, 'fetch_arxiv', return_value=[kept, skipped, old]), \
                    contextlib.redirect_stdout(output), \
                    contextlib.redirect_stderr(io.StringIO()):
                app.print_authors('Test_Author', 4, app.Format.NsfProposal,
                                  use_ads=False, use_inspire=False,
                                  collaboration_review=review)
            return output.getvalue()

        out = run(self.path)
        self.assertNotIn('Excluded', out)
        self.assertNotIn('New Institute', out)
        self.assertIn('Old Institute', out)
        self.assertIn(f'3/4/{year - 1}', out)
        self.assertEqual(len(self.rows()), 1)
        rows = self.rows()
        rows[0]['omit'] = 'N'
        self.save_rows(rows)
        self.assertIn('Excluded', run(self.path))
        self.assertIn('New Institute', run(self.path))
        self.assertIn('Excluded', run(None))

    def test_fetchers_capture_metadata(self):
        metadata = {
            'control_number': 2717996,
            'titles': [{'title': 'Waveform Modelling for LISA'}],
            'earliest_date': '2023-11-02',
            'authors': [{'full_name': 'Afshordi, Niayesh'}],
            'author_count': 146,
            'collaborations': [{'value': 'LISA Consortium Waveform Working Group'}],
            'arxiv_eprints': [{'value': '2311.01300v2'}],
            'external_system_identifiers': [{'schema': 'ADS', 'value': '2024TestA'}],
        }
        with patch.object(app, 'get_json', return_value={
                'hits': {'hits': [{'metadata': metadata}]}}) as get, \
                patch.object(app, 'fetch_inspire_institutions', return_value={}):
            p, = app.fetch_inspire('G.Lovelace.1', 2022)
        self.assertIn('collaborations.value', get.call_args.args[1]['fields'])
        self.assertEqual(p.first_author, 'Niayesh Afshordi')
        self.assertEqual(p.author_count, 146)
        self.assertEqual(p.collaborations,
                         {'LISA Consortium Waveform Working Group'})
        self.assertIn('arxiv:2311.01300', p.ids)
        self.assertIn('ads:2024TestA', p.ids)
        doc = {'bibcode': '2024TestA', 'pubdate': '2024-01-00',
               'title': ['Waveform Modelling for LISA'],
               'author': ['LISA Collaboration', 'Afshordi, Niayesh'],
               'author_count': 146, 'identifier': ['arXiv:2311.01300v1']}
        with patch.object(app, 'get_json', return_value={
                'response': {'docs': [doc], 'numFound': 1}}), \
                patch.object(app, 'fetch_ads_institutions', return_value={}):
            p, = app.fetch_ads('test-orcid', 'test-token', 2022)
        self.assertEqual(p.first_author, 'Niayesh Afshordi')
        self.assertTrue(app.likely_full_collaborations(p))
        self.assertIn('arxiv:2311.01300', p.ids)


if __name__ == '__main__':
    unittest.main()
