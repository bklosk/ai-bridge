"""Tests for ai-bridge MCP server."""

from unittest.mock import MagicMock, patch

import server


# --- ping & status ---


class TestPing:
    def test_returns_pong(self):
        assert server.ping() == "pong"


class TestGetStatus:
    def test_returns_running_string(self):
        result = server.get_status()
        assert isinstance(result, str)
        assert "running" in result


# --- bulletin_board_send validation ---


class TestBulletinBoardSend:
    def test_empty_content(self):
        assert "Error" in server.bulletin_board_send("")

    def test_whitespace_content(self):
        assert "Error" in server.bulletin_board_send("   ")

    def test_content_too_long(self):
        result = server.bulletin_board_send("a" * (server.MAX_CONTENT_LENGTH + 1))
        assert "Error" in result
        assert "too long" in result

    def test_negative_user_id(self):
        result = server.bulletin_board_send("hello", user_id=-1)
        assert "Error" in result
        assert "user_id" in result

    def test_zero_user_id(self):
        result = server.bulletin_board_send("hello", user_id=0)
        assert "Error" in result

    @patch("server.get_connection")
    def test_success(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (42,)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)

        result = server.bulletin_board_send("hello world")
        assert "id=42" in result

    @patch("server.get_connection", side_effect=RuntimeError("db down"))
    def test_db_error_returns_error_string(self, _mock):
        result = server.bulletin_board_send("hello")
        assert "Error" in result
        assert "db down" in result


# --- bulletin_board_read limit clamping ---


class TestBulletinBoardRead:
    @patch("server.get_connection")
    def test_limit_clamped_to_min(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)

        server.bulletin_board_read(limit=0)
        args = mock_cursor.execute.call_args[0][1]
        assert args == (1,)

    @patch("server.get_connection")
    def test_limit_clamped_to_max(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)

        server.bulletin_board_read(limit=99999)
        args = mock_cursor.execute.call_args[0][1]
        assert args == (5000,)

    @patch("server.get_connection", side_effect=RuntimeError("db down"))
    def test_db_error_returns_error_list(self, _mock):
        result = server.bulletin_board_read()
        assert isinstance(result, list)
        assert "error" in result[0]


# --- private_message_send validation ---


class TestPrivateMessageSend:
    def test_empty_content(self):
        assert "Error" in server.private_message_send(1, 2, "")

    def test_content_too_long(self):
        result = server.private_message_send(1, 2, "a" * (server.MAX_CONTENT_LENGTH + 1))
        assert "Error" in result
        assert "too long" in result

    def test_negative_from_user_id(self):
        result = server.private_message_send(-1, 2, "hello")
        assert "Error" in result
        assert "from_user_id" in result

    def test_zero_to_user_id(self):
        result = server.private_message_send(1, 0, "hello")
        assert "Error" in result
        assert "to_user_id" in result


# --- private_message_read validation ---


class TestPrivateMessageRead:
    def test_negative_user_id(self):
        result = server.private_message_read(-1)
        assert isinstance(result, list)
        assert "error" in result[0]

    def test_zero_user_id(self):
        result = server.private_message_read(0)
        assert isinstance(result, list)
        assert "error" in result[0]
