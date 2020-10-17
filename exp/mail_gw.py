#!/usr/bin/env python3

import email
import imaplib

IMAP_SERVER = "imap.gmail.com"


def read_secure_file(filename: str):
    with open("../secret/" + filename) as f:
        line = f.read()

    return line.strip()


def main():
    imap_username = read_secure_file("imap_username")
    imap_passwd = read_secure_file("imap_passwd")

    server = imap_login(imap_username, imap_passwd)

    handle_mail(server)
    server.close()
    server.logout()


def imap_login(username: str, passwd: str):
    server = imaplib.IMAP4_SSL(IMAP_SERVER)
    server.login(username, passwd)
    server.select("inbox")

    return server


def handle_mail(server):
    server.select()

    typ, data = server.search(None, "ALL")
    for num in data[0].split():
        typ, data = server.fetch(num, "(RFC822)")

        print(f"Message {num}")
        msg = email.message_from_bytes(data[0][1])
        print("From   :", msg["from"])
        print("Subject:", msg["subject"])
        print("Body:")
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                print(part.get_payload())


if __name__ == "__main__":
    main()
