import unittest
from unittest.mock import AsyncMock, patch

import httpx

from backend.app.extractor import extract_tiktok_fallback


class TikTokFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def run_responses(self, payloads):
        responses = [httpx.Response(200, json=p, request=httpx.Request(
            "GET", "https://www.tikwm.com/api/")) for p in payloads]
        request = AsyncMock(side_effect=responses)
        with patch("backend.app.extractor.httpx.AsyncClient.request", request), patch(
            "backend.app.extractor.asyncio.sleep", new_callable=AsyncMock
        ):
            result = await extract_tiktok_fallback("https://www.tiktok.com/@user/video/123")
        return result, request

    async def test_hd_failure_uses_standard_video(self):
        result, request = await self.run_responses([
            {"code": -1, "msg": "HD video preparing"},
            {"code": 0, "data": {"id": "123", "play": "https://cdn.example/video.mp4"}},
        ])
        self.assertTrue(result["success"])
        self.assertEqual(result["formats"][0]["format_id"], "play")
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args.kwargs["data"]["hd"], 0)

    async def test_missing_stream_is_not_success(self):
        result, _ = await self.run_responses([
            {"code": 0, "data": {"id": "123"}},
            {"code": 0, "data": {"id": "123"}},
        ])
        self.assertIsNone(result)

    async def test_hd_success_does_not_retry(self):
        result, request = await self.run_responses([
            {"code": 0, "data": {"id": "123", "hdplay": "https://cdn.example/hd.mp4"}},
        ])
        self.assertTrue(result["success"])
        self.assertEqual(request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
