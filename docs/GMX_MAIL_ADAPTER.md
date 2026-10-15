# GMX-Mailadapter für F.R.I.D.A.Y.

Autor: RogueKI. Der Adapter ist optional und standardmäßig offline. Er ändert keine Installation oder Konfiguration in `rogue-friday`.

## Betriebsarten

| Modus | Verhalten |
| --- | --- |
| `mock` | Synthetische Nachricht aus `fixtures/mail/adapter_message.json`; keine Zugangsdaten und kein Netzwerk. |
| `read_only` | Eine explizit angegebene Mailbox und UID per IMAP/TLS lesen. `EXAMINE` und `BODY.PEEK` setzen kein Gelesen-Flag. |
| `live` | Dieselbe Leseoperation; SMTP-Versand nur über die separate Python-Funktion `send_message`. |

Das Hermes-Plugin `friday-gmx-mail` registriert ausschließlich `friday_gmx_read_uid`. Für echte Lesezugriffe müssen `FRIDAY_SKILLS_ROOT`, `FRIDAY_GMX_ALLOW_READ=1`, `FRIDAY_GMX_ADDRESS` und `FRIDAY_GMX_APP_PASSWORD` im Prozess gesetzt sein. Ohne `FRIDAY_GMX_ALLOW_READ=1` verweigert es den Zugriff. Das Passwort ist ein GMX-App-Passwort, das weder im Repository noch in Logs abgelegt wird. Das Plugin bietet absichtlich **kein Sendetool**.

Direkte Python-Integration: `read_message(mailbox, uid, mode="read_only", credentials=GMXCredentials(...), use_stdlib_transport=True)`. Der Standardmodus nutzt nur die synthetische Fixture. Ein injizierter Transport ist für isolierte Tests vorgesehen. Es gibt keine automatische Postfachsuche, keine Markierung als gelesen und keinen Abruf beliebiger Anhänge. Vollständige Nachrichten über 65.536 Byte werden abgewiesen. Nur höchstens 16.000 Zeichen des ersten `text/plain`-Teils werden als **untrusted** zurückgegeben. HTML wird nicht ausgeführt oder zurückgegeben; Anhänge erscheinen nur als Metadaten mit Typ- und Größenkennzeichnung. Die Instruktionsmuster-Erkennung ist ein Hinweis, keine vollständige Prompt-Injection-Abwehr.

`send_message` erfordert `live`, einen expliziten GMX-Absender, genau einen Empfänger, eine frische `mail.send`-Schreibfähigkeit, ein hostseitiges `ApprovalLedger` samt einmaliger Grant-ID, einen stabilen Idempotenzschlüssel, ein persistentes SQLite-Journal und einen expliziten SMTP-Transport. Das frühere `approval`-Mapping wird nicht mehr akzeptiert. Die Freigabe wird atomar vor dem Journal-Eintrag und dem einmaligen SMTP-Versuch verbraucht. Ein Timeout ergibt `unknown_outcome`; der Adapter wiederholt nicht. Auch ein neuer Schlüssel für denselben Fingerprint wird blockiert. Vor einem weiteren Versuch muss der Operator die Zustellung im Postfach/Provider nachvollziehen. `accepted_by_smtp` belegt nur die Annahme durch den SMTP-Server, nicht die Zustellung beim Empfänger. Die Herkunft der Operatorentscheidung und der Schutz des Ledger-Pfads sind Aufgaben des Hosts; siehe [Freigabegrenze](APPROVAL_LEDGER.md).

Für echten Betrieb sind Mailbox-Aktivierung und Zugangsdaten außerhalb des Repositories nötig. Die Implementierung verwendet GMX `imap.gmx.net:993` mit TLS und `mail.gmx.net:587` mit STARTTLS. [GMX-Serverdaten](https://hilfe.gmx.net/pop-imap/imap/imap-serverdaten.html), [GMX-App-Passwort](https://hilfe.gmx.net/sicherheit/2fa/anwendungsspezifisches-passwort.html). IMAP-UID und `BODY.PEEK` folgen [RFC 9051](https://www.rfc-editor.org/rfc/rfc9051.html). SMTP-Übertragung ist in [RFC 5321](https://www.rfc-editor.org/rfc/rfc5321.html) beschrieben.

## Verifikation und Grenzen

`python -m unittest discover -s tests -p 'test_*gmx_mail*.py' -v` prüft Mock, Eingabegrenzen, HTML-/Anhangsbehandlung, fehlende/abgelaufene/falsch gebundene Freigabe, Journal-Deduplizierung, unbekanntes Ergebnis und Plugin-Sperre. Die Tests verwenden kein reales GMX-Konto und keine Netzwerkverbindung. Anbieter-Interoperabilität, IMAP-UIDVALIDITY, tatsächliche Zustellung und ein echter Hermes-Profillauf sind damit nicht bewiesen. Der stdlib-IMAP-Client fordert eine begrenzte Partial-Fetch-Antwort an; ein bösartiger Server könnte dennoch vor der lokalen Größenprüfung mehr Speicher verbrauchen.
