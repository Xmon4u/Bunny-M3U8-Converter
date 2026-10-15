import unittest
import urllib.error
from unittest import mock

from bunny_m3u8 import (
    DirectPlaylist,
    Invalid,
    PlayRef,
    convert_job,
    extract_m3u8,
    parse_inputs,
)

VID = "61e4f637-dbd1-4dc1-b68a-9acdec0e6988"
PLAY = f"https://player.mediadelivery.net/play/780046/{VID}"
EMBED = f"https://iframe.mediadelivery.net/embed/780046/{VID}"


class ParseTests(unittest.TestCase):
    def test_single_play_url(self) -> None:
        jobs = parse_inputs(PLAY + " \n")
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        assert isinstance(job, PlayRef)
        self.assertEqual(job.library_id, "780046")
        self.assertEqual(job.video_id, VID)
        self.assertEqual(job.host, "player")
        self.assertEqual(job.kind, "play")

    def test_many_messy_links(self) -> None:
        text = f"""
        1. {PLAY}
        <iframe src="https://player.mediadelivery.net/embed/12/{VID}?autoplay=true&amp;loop=true"></iframe>
        player.mediadelivery.net/play/9/{VID.upper()}/
        https://vz-abc.b-cdn.net/{VID}/playlist.m3u8
        this is not a link
        """
        jobs = parse_inputs(text)
        self.assertEqual(len(jobs), 5)
        self.assertIsInstance(jobs[0], PlayRef)
        embed = jobs[1]
        assert isinstance(embed, PlayRef)
        self.assertEqual(embed.kind, "embed")
        self.assertIn("autoplay=true", embed.query)
        self.assertIn("loop=true", embed.query)
        bare = jobs[2]
        assert isinstance(bare, PlayRef)
        self.assertEqual(bare.video_id.lower(), VID)
        self.assertIsInstance(jobs[3], DirectPlaylist)
        self.assertIsInstance(jobs[4], Invalid)

    def test_token_query_kept(self) -> None:
        url = f"{PLAY}?token=abc123&expires=1456761770"
        job = parse_inputs(url)[0]
        assert isinstance(job, PlayRef)
        self.assertEqual(job.query, "token=abc123&expires=1456761770")
        pages = job.candidate_urls()
        self.assertTrue(pages[0].startswith("https://player.mediadelivery.net/embed/"))
        self.assertIn("token=abc123", pages[0])
        self.assertIn("iframe.mediadelivery.net/embed/", pages[1])

    def test_iframe_host_tries_legacy_first(self) -> None:
        job = parse_inputs(EMBED)[0]
        assert isinstance(job, PlayRef)
        self.assertTrue(job.candidate_urls()[0].startswith("https://iframe.mediadelivery.net/"))


class ExtractTests(unittest.TestCase):
    def test_direct_playlist_and_title(self) -> None:
        page = f"""
        <meta property="og:title" content="Demo &amp; Show">
        <video src="https://vz-abc.b-cdn.net/{VID}/playlist.m3u8"></video>
        """
        self.assertEqual(
            extract_m3u8(page, VID),
            f"https://vz-abc.b-cdn.net/{VID}/playlist.m3u8",
        )

    def test_prefers_signed_playlist(self) -> None:
        signed = (
            f"https://vz-abc.b-cdn.net/bcdn_token=abc&expires=10&token_path=%2F{VID}%2F"
            f"/{VID}/playlist.m3u8"
        )
        plain = f"https://vz-abc.b-cdn.net/{VID}/playlist.m3u8"
        page = f'<source src="{plain}"><source src="{signed}">'
        self.assertEqual(extract_m3u8(page, VID), signed)

    def test_thumbnail_fallback_custom_host(self) -> None:
        page = f'<meta property="og:image" content="https://videos.example.com/{VID}/thumbnail.jpg">'
        self.assertEqual(
            extract_m3u8(page, VID),
            f"https://videos.example.com/{VID}/playlist.m3u8",
        )

    def test_escaped_slashes(self) -> None:
        page = f'https:\\/\\/vz-abc.b-cdn.net\\/{VID}\\/playlist.m3u8'
        self.assertEqual(
            extract_m3u8(page, VID),
            f"https://vz-abc.b-cdn.net/{VID}/playlist.m3u8",
        )


class ConvertTests(unittest.TestCase):
    def test_falls_through_404_shell_to_next_player(self) -> None:
        good = f"""
        <meta property="og:title" content="Episode 1">
        <video src="https://vz-abc.b-cdn.net/{VID}/playlist.m3u8"></video>
        """

        def fetch(url: str) -> str:
            if "iframe.mediadelivery.net" in url:
                return "<html><title> 404 </title><body>missing</body></html>"
            if "player.mediadelivery.net/embed" in url:
                return good
            raise AssertionError(url)

        job = parse_inputs(EMBED)[0]
        result = convert_job(job, fetch=fetch)
        self.assertTrue(result.ok)
        self.assertEqual(result.title, "Episode 1")
        self.assertIn("playlist.m3u8", result.m3u8)

    def test_real_http_404_then_success(self) -> None:
        def fetch(url: str) -> str:
            if "player.mediadelivery.net/embed" in url:
                raise urllib.error.HTTPError(url, 404, "missing", hdrs=None, fp=None)
            if "iframe.mediadelivery.net" in url:
                return f"https://vz-z.b-cdn.net/{VID}/thumbnail.jpg"
            raise AssertionError(url)

        job = parse_inputs(PLAY)[0]
        result = convert_job(job, fetch=fetch)
        self.assertTrue(result.ok)
        self.assertEqual(result.m3u8, f"https://vz-z.b-cdn.net/{VID}/playlist.m3u8")

    def test_direct_playlist_skips_network(self) -> None:
        url = f"https://vz-abc.b-cdn.net/{VID}/playlist.m3u8"
        result = convert_job(parse_inputs(url)[0], fetch=mock.Mock(side_effect=AssertionError("network")))
        self.assertTrue(result.ok)
        self.assertEqual(result.m3u8, url)

    def test_invalid_does_not_raise(self) -> None:
        result = convert_job(parse_inputs("hello there")[0])
        self.assertFalse(result.ok)
        self.assertIn("Bunny", result.error)

    def test_all_missing(self) -> None:
        def fetch(url: str) -> str:
            raise urllib.error.HTTPError(url, 404, "missing", hdrs=None, fp=None)

        result = convert_job(parse_inputs(PLAY)[0], fetch=fetch)
        self.assertFalse(result.ok)
        self.assertIn("not found", result.error)


if __name__ == "__main__":
    unittest.main()
