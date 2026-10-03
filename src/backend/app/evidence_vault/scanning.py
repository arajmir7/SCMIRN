"""Fail-closed ClamAV scanner adapter for private evidence uploads."""
from __future__ import annotations

import socket
import struct


class ScannerUnavailable(RuntimeError):
    """The configured scanner could not complete a scan."""


class MalwareDetected(RuntimeError):
    """The scanner rejected the uploaded content."""


class ClamAVScanner:
    """Use ClamAV's INSTREAM protocol over a configured Unix or TCP socket."""

    def __init__(self, *, host: str | None = None, port: int = 3310, unix_socket: str | None = None, timeout: float = 5.0):
        if not unix_socket and not host:
            raise ValueError("A ClamAV Unix socket or host is required.")
        self.host = host
        self.port = int(port)
        self.unix_socket = unix_socket
        self.timeout = float(timeout)

    def _connect(self):
        try:
            if self.unix_socket:
                connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                connection.settimeout(self.timeout)
                connection.connect(self.unix_socket)
                return connection
            return socket.create_connection((self.host, self.port), timeout=self.timeout)
        except OSError as exc:
            raise ScannerUnavailable("Malware scanner is unavailable.") from exc

    @staticmethod
    def _read_response(connection) -> str:
        response = bytearray()
        try:
            while len(response) < 4096:
                chunk = connection.recv(512)
                if not chunk:
                    break
                if b"\0" in chunk:
                    response.extend(chunk.split(b"\0", 1)[0])
                    break
                response.extend(chunk)
        except OSError as exc:
            raise ScannerUnavailable("Malware scanner response could not be read.") from exc
        if not response or len(response) >= 4096:
            raise ScannerUnavailable("Malware scanner response was invalid.")
        try:
            return response.decode("ascii", errors="strict").strip()
        except UnicodeDecodeError as exc:
            raise ScannerUnavailable("Malware scanner response was invalid.") from exc

    def _command(self, payload: bytes) -> str:
        connection = self._connect()
        try:
            connection.sendall(payload)
            return self._read_response(connection)
        except OSError as exc:
            raise ScannerUnavailable("Malware scanner request failed.") from exc
        finally:
            connection.close()

    def scan(self, path: str) -> str:
        version = self._command(b"zVERSION\0")
        if not version.startswith("ClamAV "):
            raise ScannerUnavailable("Malware scanner version could not be verified.")
        connection = self._connect()
        try:
            connection.sendall(b"zINSTREAM\0")
            with open(path, "rb") as evidence_file:
                while True:
                    chunk = evidence_file.read(64 * 1024)
                    if not chunk:
                        break
                    connection.sendall(struct.pack("!I", len(chunk)))
                    connection.sendall(chunk)
            connection.sendall(struct.pack("!I", 0))
            response = self._read_response(connection)
        except OSError as exc:
            raise ScannerUnavailable("Malware scan did not complete.") from exc
        finally:
            connection.close()
        if response.endswith("OK"):
            return version
        if "FOUND" in response:
            raise MalwareDetected("Uploaded evidence was rejected by malware scanning.")
        raise ScannerUnavailable("Malware scanner returned an unrecognized result.")
