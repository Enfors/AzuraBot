#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import email
import imaplib
import smtplib
import time

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.message import MIMEMessage

from enforsml.text import nlp, utils

IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"


def read_secure_file(filename: str):
    with open("../secret/" + filename) as f:
        line = f.read()

    return line.strip()


def main():
    imap_username = read_secure_file("imap_username")
    imap_passwd = read_secure_file("imap_passwd")

    imap_server = imap_login(imap_username, imap_passwd)

    bot = DemoBot()

    while True:
        handle_mail(imap_server, bot, imap_username, imap_passwd)
        time.sleep(20)

    imap_server.close()
    imap_server.logout()


def imap_login(username: str, passwd: str):
    imap_server = imaplib.IMAP4_SSL(IMAP_SERVER)
    print(f"Logging in with username '{username}', "
          f"password '{passwd[0:2]}...{passwd[-2:-0]}'")
    imap_server.login(username, passwd)
    imap_server.select("inbox")

    return imap_server


def handle_mail(imap_server, bot, username, passwd):
    imap_server.select()
    first_line = ""

    typ, data = imap_server.search(None, "ALL")
    for num in data[0].split():
        typ, data = imap_server.fetch(num, "(RFC822)")

        msg = email.message_from_bytes(data[0][1])
        original = msg
        print("==== New message ==================================")
        print("From:", msg["from"])
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                body = body.decode("utf-8")

                first_line = body.split("\n")[0]

        if len(first_line) == 0:
            print("Coulnd't find any contents in mail body.")
            continue

        question = first_line
        print("Question: " + question)
        response = bot.get_response(first_line)
        print("Answer: " + response)

        new = MIMEMultipart("mixed")
        # body = MIMEMultipart("alternative")

        # text = f"Din fråga: {first_line}\n\nSvar: {response}\n"
        html = f"""\
        <html>
          <body>
            <p>Du skrev: {question}</p>
            <p>Svar: {response}</p>
          </body>
        </html>
        """

        # new.attach(body)

        new["Message-ID"] = email.utils.make_msgid()
        new["In-Reply-To"] = original["Message-ID"]
        new["References"] = original["Message-ID"]
        try:
            new["Subject"] = "Re: " + original["Subject"]
        except TypeError:
            new["Subject"] = "Re: Din fråga"

        new["To"] = original["Reply-To"] or original["From"]
        new["From"] = "dialog4u.gateway@gmail.com"

        # text_part = MIMEText(text, "plain")
        html_part = MIMEText(html, "html")
        # new.attach(text_part)
        new.attach(html_part)

        new.attach(MIMEMessage(original))

        smtp_server = smtplib.SMTP_SSL(SMTP_SERVER, 465)
        smtp_server.login(username, passwd)
        smtp_server.sendmail("dialog4u.gateway@gmail.com",
                             original["Reply-To"] or original["From"],
                             new.as_string().encode("ascii"))
        smtp_server.quit()

        imap_server.store(num, "+FLAGS", "\\Deleted")
        imap_server.expunge()


def test_bot():
    bot = DemoBot()

    print("Hej! Jag kan svara på frågor om Shorinji Kempo.")

    while True:
        user_input = input("Din fråga: ").strip()
        if len(user_input) == 0:
            break

        response = bot.get_response(user_input)
        print(response)


class DemoBot():

    def __init__(self):
        self.all_intents = []
        callcenter_training_data = [
            # Hej / Vad kan du göra?
            ["Hej",
             "Tjena",
             "Hallå",
             "Vad kan du göra",
             "Vad kan du hjälpa till med",
             "Vad är du till för",

             "Hej! Jag är Call4U:s chatbot. Jag kan svara på diverse frågor "
             "om öppettider, hjälpa till med att pausa prenummerationer, "
             "och så vidare. "],

            # Öppettider
            ["När har ni öppet",
             "Vad har ni för öppettider",
             "Vilka är era öppet tider",
             "När öppnar ni",
             "Öppettider",
             "Öppet tider",

             "Vi har öppet vardagar 08:00 - 20:00."],

            # Öppet på helgen?
            ["Är det stängt på helgen",
             "Har ni inte öppet på helgen",
             "Är det stängt hela helgen",
             "Vilka öppettider har ni på helgen",

             "Vi har inte öppet på helgen - men jag finns här dygnet runt! "
             "Skicka gärna dina frågor till mig, så ska jag försöka besvara "
             "dem. Kan jag inte det, så kommer personalen att svara dig när "
             "vårt kundcenter öppnar. "],

            # Kontaktuppgifter
            ["Vilka är era kontaktuppgifter",
             "Kan jag få era kontakt uppgifter",
             "Vad är ert telefonnummer",
             "Vad har ni för telefon nummer",
             "Kan man ringa er",

             "Vårt telefonnummer är 020-1234567 - du är välkommen att ringa!"],

            # Pausa en pernummeration
            ["Jag vill pausa en prenummeration",
             "Jag ska på semester och vill pausa en prenummeration",
             "Jag vill göra ett uppehåll i en prenummeration",

             "Inga problem, vi kan pausa en prenummeration ett tag. "
             "Vilken tidning gäller det?"],

            # "Jag vill pausa Svenska Dagbladet"
            ["Svenska Dagbladet",
             "Svenska dagbladet",
             "svenska dagbladet",
             "svenskan",
             "Sydsvenskan",
             "sydsvenskan",
             "syd svenskan",

             "Okej. Då pausar jag din prenummerationen kopplad till din "
             "epostadress tills vidare. "
             "Hör av dig när du vill att den återupptas igen."],

            # Återuppta prenummeration
            ["Jag vill återuppta min prenummeration",
             "Nu vill jag ha tidningen igen",
             "Kan jag få åter uppta prenummerationen igen",

             "Absolut! Från och med imorgon kommer du att få din tidning hem "
             "i brevlådan igen. Välkommen tillbaka!"]
        ]

        kempo_training_data = [
            # Hej
            ["Hej",
             "Tjena",
             "Hallå",
             "Morsning",
             "start",
             "/start",
             "Hej!"],

            # Vad är Shorinji Kempo
            ["Vad är Shorinji Kempo",
             "Vad är Shorinji Kempo för något",
             "Vad är Shorinji Kempo för slags kampsport",
             "Shorinji Kempo är en mångsidig japansk kampsport, "
             "där vi bland annat använder sparkar, slag, kast "
             "och losstagningar (när man blir fasthållen). "
             '<iframe width="800" height="450" '
             'src="https://www.youtube.com/embed/fr1pk8r_-Vo" '
             'rameborder="0" allow="accelerometer; autoplay; '
             'encrypted-media; gyroscope; picture-in-picture" '
             'allowfullscreen></iframe>'],

            ["Vad kan du göra",
             "Vad har du för funktion",
             "Vad är du till för",
             "Jag kan svara på frågor om kampsporten Shorinji Kempo, "
             "och om Shorinji Kempo-klubben i Karlstad."],

            # Hur blir man medlem
            ["Hur blir man medlem",
             "Hur blir man medlem i Shorinji Kempo",
             "Vad krävs för att bli medlem",
             "Hur blir man medlem i klubben",
             "Hur går man med i Shorinji Kempo",
             "Hur går man med i klubben",
             "Hur anmäler man sig",
             "Var kan jag anmäla mig",
             "Måste man anmäla sig",
             "När tar ni in nya medlemmar",
             "Hur gör jag för att börja träna?"
             "Information om hur man blir medlem hittar du på "
             "<a href='http://shorinjikempo.net/traning/borja-trana'>"
             "sidan \"Börja träna\" på vår hemsida</a>."],

            # Är det roligt
            ["Är det roligt att träna Shorinji Kempo",
             "Är Shorinji Kempo roligt",
             "Är det kul att träna",
             "Det är jätteroligt att träna Shorinji Kempo!"],

            # Vem grundade Shorinji Kempo
            ["Vem grundade Shorinji Kempo",
             "Vem var det som grundade Shorinji Kempo",
             "Vem är Shorinji Kempos grundare",
             "Vem var det som startade Shorinji Kempo",
             "Vem var det som uppfann Shorinji Kempo",
             "Vem hittade på Shorinji Kempo",
             "Vem startade Shorinji Kempo",
             "Shorinji Kempo grundades av So Doshin."],

            # Skillnad mot andra kampsporter
            ["Vad skiljer Shorinji Kempo från andra kampsporter",
             "Vad är det för skillnad mellan Shorinji Kempo och "
             "andra kampsporter",
             "Vad är speciellt med Shorinji Kempo",
             "Vad är det som gör Shorinji Kempo unikt",
             "Varför ska jag träna just Shorinji Kempo",
             "Vad har Shorinji Kempo för kännetecken",
             "Vad är det för skillnad mellan Shorinji Kempo och "
             "karate",
             "Shorinji Kempo brukar kallas \"Den tänkande människans "
             "kampsport\", eftersom vi lägger relativt stor vikt "
             "vid filosofi."],

            # Finns det sparkar och slag
            ["Finns det sparkar och slag i Shorinji Kempo",
             "Finns det slag i Shorinji Kempo",
             "Slår man i Shorinji Kempo",
             "Finns det sparkar i Shorinji Kempo",
             "Sparkar man i Shorinji Kempo",
             "Shorinji Kempo innehåller sparkar, slag, "
             "losstagningar, nedtagningar och kast."],

            # Gör det ont
            ["Gör det ont att träna Shorinji Kempo",
             "Får man ont av att träna",
             "Gör det ont när man tränar",
             "Hur ont gör det att träna",
             "Vissa tekniker som tränas i vuxengruppen kan göra lite "
             "ont, så det är viktigt att vi är försiktiga med "
             "varandra. Dessa tekniker tränas dock inte i "
             "juniorgruppen."],

            # Vad kostar det
            ["Vad kostar det att vara medlem",
             "Vad kostar det att bli medlem i klubben",
             "Vad kostar träningen",
             "Hur mycket kostar träningen",
             "Vad kostar medlemsskapet",
             "Vad kostar det att vara med",
             "Hur mycket kostar det att träna Shorinji Kempo",
             "Är det dyrt att vara med",
             "Hur dyrt är det att träna",
             "Alla priser finns på "
             "<a href='http://shorinjikempo.net/traning/borja-trana'>"
             "vår hemsida</a>."],

            # Provträna gratis
            ["Kan man provträna gratis",
             "Måste man bli medlem innan man tränar",
             "Kan man prova innan man blir medlem",
             "Kan man testa utan att det kostar något",
             "Måste man betala om man bara vill testa",
             "Om man betalar månadsavgiften, så kan man provträna en "
             "månad utan att behöva betala träningsavgift."],

            # Var ligger dojon
            ["Var ligger träningslokalen",
             "Var finns dojon",
             "Var finns er dojo",
             "Var ligger er dojo",
             "Var finns er träningslokal",
             "Var håller ni till",
             "Var tränar ni",
             "Var finns ni",
             "Var brukar ni träna",
             "Var ligger klubbens träningslokal",
             "Var kan man lära sig",
             "Vart kan man lära sig",
             "Var kan man lära sig det",
             "Vi tränar i Mariebergsskolans gamla gymnastiksal, "
             "på Rosenborgsgatan 28 i Karlstad. Det ligger snett "
             "över vägen från sjukhuset.<br>"
             '<iframe src="https://www.google.com/maps/embed?pb='
             '!1m18!1m12!1m3!1d2032.6166318831747!2d13.478893316077826!'
             '3d59.37273698167405!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!'
             '4f13.1!3m3!1m2!1s0x465cb1795c9a4321%3A0x136c6cb621aa9bd!'
             '2sShorinji%20Kempo%20Karlstad%20Shibu!5e0!3m2!1ssv!2sse!'
             '4v1568641561509!5m2!1ssv!2sse"'
             'width="800" height="450" frameborder="0" style="border:0;"'
             'allowfullscreen=""></iframe>'
             "Från och med höstterminen 2020 är det meningen att vi "
             "ska börja träna i Kvarnbergsskolans nya gymnastiksal, "
             "som just nu är under byggnation. "],

            # Är det svårt
            ["Är Shorinji Kempo svårt",
             "Är det en svår sport",
             "Är det svårt att träna Shorinji Kempo",
             "Hur svårt är det",
             "Hur svårt är Shorinji Kempo",
             "Är det svårt",
             "Är det svårt att lära sig",
             "Det finns mycket att lära sig, men det är också det "
             "som gör det intressant."],

            # Träningstider
            ["Vilka träningstider har ni",
             "När tränar ni",
             "Vilka tider tränar ni",
             "Vilka dagar tränar ni",
             "När är träningarna",
             "När slutar träningarna",
             "Vilka tider tränar ni",
             "Hur länge håller träningarna på",
             "Hur många gånger tränar ni per vecka",
             "Hur många träningspass har ni",
             "Hur ofta tränar ni",
             "Hur ofta har ni träningar",
             "Hur ofta är det träning",
             "Hur ofta måste man träna",
             "Träningstiderna hittar du på "
             "<a href='http://shorinjikempo.net/traning/traningstider'>"
             "vår hemsida</a>."],

            # Åldersgränser
            ["Hur gammal måste man vara",
             "Hur gammal måste man vara för att få börja",
             "Vad har ni för åldersgränser",
             "Har ni någon åldersgräns",
             "För liten",
             "För ung",
             "Har ni barngrupp",
             "Har ni barngrupper",
             "Finns det juniorgrupp",
             "Finns det juniorgrupper",
             "Vad är juniorgruppen",
             "Tillräckligt stor",
             "Tillräckligt gammal",
             "När är man stor nog",
             "När är man gammal nog",
             "När är man för gammal",
             "Kan man bli för gammal",
             "För att träna måste man vara minst åtta år. "
             "Vi har ingen övre åldersgräns, och vi har "
             "aktiva medlemmar som är 60+. De som är under "
             "13 år tränar i juniorgruppen, resten tränar i "
             "vuxengruppen. "],

            # Måste man kunna japanska
            ["Måste man kunna japanska",
             "Behöver man lära sig japanska",
             "Får man lära sig japanska",
             "Man behöver inte kunna japanska för att träna "
             "Shorinji Kempo, men vissa ord och fraser kommer man "
             "att lära sig av sig själv."],

            # Vem är tränare
            ["Vem är tränaren",
             "Vem är instruktör",
             "Vad har ni för tränare",
             "Vilka tränare har ni",
             "Vad har er tränare för grad",
             "Vem är er sensei",
             "Vad heter er sensei",
             "Vilka är era instruktörer",
             "Vem är er instruktör",
             "Vem är Anders Pettersson",
             "Vem är Anders-sensei",
             "Vilken grad har er tränare",
             "Vilken grad har er sensei",
             "Vår huvudinstruktör heter Anders Pettersson, "
             "och han har graden rokudan - svart bälte av "
             "sjätte graden."],

            # Vad heter klubben
            ["Vad heter klubben",
             "Vad heter föreningen",
             "Vad kallas klubben",
             "Vad kallar ni er klubb",
             "Vad har klubben för namn",
             "Vad är det för namn på föreningen",
             "Föreningen heter Shorinji Kempo Karlstad Shibu, "
             "vilket betyder Karlstads Shorinji Kempo-förening."],

            # När grundades klubben
            ["När grundades klubben",
             "Vilket år grundades klubben",
             "Vem grundade klubben",
             "Vem startade klubben",
             "Vem var det som startade klubben",
             "När startades klubben",
             "Vem var det som grundade klubben",
             "Hur länge har klubben funnits",
             "Klubben grundades av bland andra Anders Pettersson, "
             "1981."],

            # Hur många medlemmar har vi
            ["Hur många medlemmar har ni",
             "Hur stort är medlemsantalet",
             "Hur många aktiva medlemmar har ni i klubben",
             "Hur många är ni",
             "I nuläget har vi c:a 40 aktiva medlemmar i vår klubb."],

            # Hur många aktiva utövare i Sverige
            ["Hur många aktiva finns det i Sverige",
             "Hur många medlemmar finns det totalt i Sverige",
             "Totalt finns det c:a 300 aktiva utövare i Sverige."],

            # Hur många klubbar finns det i Sverige
            ["Hur många klubbar finns det i Sverige",
             "Hur många föreningar finns det i Sverige",
             "Det finns ett tiotal Shorinji Kempo-föreningar i "
             "Sverige."],

            # Kontaktuppgifter
            ["Hur kontaktar man er",
             "Hur kan man kontakta er",
             "Kan man ringa till er",
             "Vad är era kontaktuppgifter",
             "Jag vill ringa er",
             "Har ni någon epostadress",
             "Har ni någon emailadress",
             "Har ni någon email-adress",
             "Vad är er email-adress",
             "Vad har Anders för telefonnummer",
             "Vad har Christer för telefonnummer",
             "Kan du Anders telefonnummer",
             "Kan du Christers telefonnummer",
             "Våra kontaktuppgifter hittar du på "
             "<a href='http://shorinjikempo.net/kontakt'>"
             "kontaktsidan på vår hemsida</a>."],

            # Hemsida
            ["Var finns er hemsida",
             "Har ni någon hemsida",
             "Vad har er hemsida för adress",
             "Vad är er hemsideadress",
             "Vår hemsida finns på <a href='http://www.shorinjikempo.net'>"
             "www.shorinjikempo.net</a>."],

            # Facebook
            ["Finns ni på Facebook",
             "Har ni någon Facebook-sida",
             "Har ni någon Facebook sida",
             "Vad är adressen till er Facebook",
             "Adressen till klubbens Facebook-sida",
             "Klubbens Facebook sida",
             "Vår Facebook-sida finns på "
             "<a href='http://www.facebook.com/ShorinjiKempoKarlstad'>"
             "www.facebook.com/ShorinjiKempoKarlstad</a>."],

            # Svart bälte
            ["Kan man få svart bälte",
             "Hur lång tid tar det att få svart bälte",
             "När får man svart bälte",
             "Hur mycket träning krävs det för att få svart bälte",
             "Om man ligger i, kan man ta svart bälte efter ungefär "
             "fem års träning."],

            # Behöver man ta med sig något till träningen
            ["Behöver man ta med sig något till träningen",
             "Vad behöver man ta med sig till träning",
             "Är det något man ska ta med sig",
             "Behöver man egen utrustning",
             "Ska jag ta med mig något till träningen",
             "Behöver man ha något med sig när man ska träna",
             "Det enda man behöver är lämpliga träningskläder. Man "
             "kan köpa en traditionell träningsdräkt - en dogi - via "
             "klubben, men innan dess kan man ha vanliga träningskläder "
             "på sig när man tränar. Det kan dock vara en bra ide att "
             "ha en vattenflaska med sig."],

            # Behöver man skor
            ["Behöver man ha skor",
             "Har man skor på sig",
             "Får man ha skor när man tränar",
             "Shorinji Kempo tränar man barfota,"],

            # Dogi
            ["Var kan man köpa kläder",
             "Måste man ha gi",
             "Kan man träna i vanliga kläder",
             "Kan man använda vanliga träningskläder",
             "Tränar ni med gi eller no-gi",
             "När man börjar, så kan man använda vanliga "
             "träningskläder. Sen kan man köpa en traditionell "
             "träningsdräkt - en dogi - genom klubben."],

            # Skador
            ["Är det lätt att skada sig",
             "Hur stor är skaderisken",
             "Är det farligt att träna",
             "Kan man skada sig",
             "Hur ofta blir folk skadade",
             "Hur vanligt är det med skador",
             "Jag är rädd att bli skadad",
             "Kan man bli skadad",
             "Skaderisken är relativt låg i Shorinji Kempo, jämfört "
             "med t.ex. fotboll eller innebandy."],

            # Hur många bälten finns det
            ["Hur många bälten finns det",
             "Vad finns det för bälten",
             "Får man ta bälten",
             "Alla börjar med vitt bälte. Om man är under 10 år kan "
             "man sedan ta gult bälte (detta bälte hoppar man över "
             "om man är över 10 år). Sedan kommer det grönt bälte i "
             "tre grader (alltså tre separata graderingar), sedan "
             "brunt i tre grader, och till sist svart i nio grader."],

            # Nybörjargrupp
            ["Har ni nybörjargrupper",
             "När tränar nybörjare",
             "Har ni träning för nybörjare",
             "När har ni nybörjarintag",
             "Kan man börja mitt i terminen",
             "Kan man börja mitt i en termin",
             "När tränar nybörjarna",
             "I Shorinji Kempo så tränar alla tillsammans, oavsett "
             "erfarenhetsnivå. Det ingår i konceptet att de erfarna "
             "hjälper till att instruera nybörjarna, så alla tränar "
             "på samma tider. Därför kan man börja träna även mitt i "
             "en termin."],

            # Familjerabatt
            ["Har ni familjerabatt",
             "Finns det familje rabatt",
             "Kan man få familjerabatt",
             "Kan man få rabatt",
             "Har ni familjerabatter",
             "Har ni familje rabatter",
             "Det finns många familjer som tränar tillsammans hos "
             "oss, och det tycker vi är mycket positivt. Därför "
             "erbjuder vi familjerabatter - se "
             "<a href='http://www.shorinjikempo.net/traning/"
             "traningsavgifter>vår hemsida</a> för alla detaljer."],

            # Bussar
            ["Går det bussar till träningslokalen",
             "Vilken buss ska man ta till dojon",
             "Vilken buss går till träningen",
             "Man kan förslagsvis åka buss nummer 3 från torget, "
             "men alla bussar som går till Sjukhuset stannar nära "
             "träningslokalen."],

            # Parkering
            ["Finns det parkeringsplatser vid träningslokalen",
             "Går det att parkera",
             "Var kan man pakera",
             "Är det ont om parkeringsplatser",
             "Är det ont om pakering",
             "Hur många parkeringsplatser finns det",
             "Är det svårt att hitta parkering",
             "Brukar det finnas lediga parkeringsplatser",
             "Vi brukar parkera mellan träningslokalen och "
             "Mariebergsskolan, precis utanför vår ytterdörr. "
             "Ibland kan det hända att det blir fullt där, då kan "
             "man lämpligtvis parkera på Värmlandsarkivs parkering."],

            # Tävlingar
            ["Brukar ni tävla",
             "Finns det tävlingar i Shorinji Kempo",
             "Hur går tävlingar till i Shorinji Kempo",
             "Hur fungerar det med tävlingar",
             "Hur funkar tävlingar",
             "Hur fungerar tävlandet",
             "Kan man tävla",
             "Hur tävlar man i Shorinji Kempo",
             "I Shorinji Kempo finns det något som kallas \"embu\". "
             "En embu är en slags koreograferad kamp, där det är "
             "förutbestämt vad varje deltagare ska göra. "
             "Detta är vår tävlingsform - den som visar den bästa "
             "embun vinner. I videon nedan finns ett exampel - "
             "det är det vinnande bidraget i Europamästerskapet 2019, "
             "i klassen 3:e dan och uppåt. "
             '<iframe width="800" height="450" '
             'src="https://www.youtube.com/embed/BiG7KwBsEzk?start=60" '
             'frameborder="0" allow="accelerometer; autoplay; '
             'encrypted-media; gyroscope; picture-in-picture" '
             'allowfullscreen></iframe>'],

            # Hur ofta tävlar vi
            ["Hur ofta är det tävling",
             "Hur ofta brukar ni tävla",
             "Hur ofta tävlar ni",
             "Hur ofta är det tävlingar",
             "När är det tävlingar",
             "Är det många tävlingar",
             "Vi brukar delta i SM varje år, och vi har även lösa "
             "planer på att arrangera egna klubbtävlingar."],

            # Sparring
            ["Har ni sparring",
             "Brukar ni sparras",
             "Kör ni med sparring",
             "Tränar ni sparring",
             "Tränar ni med sparring",
             "Tränar ni randori",
             "Brukar ni träna randori",
             "Sparring inom Shorinji Kempo - och inom japanska "
             "kampsporter i allmänhet - kallas randori, och det är "
             "något vi tränar regelbundet i vuxengruppen."],

            # Barngrupp
            ["Har ni barngrupper",
             "Har ni någon barngrupp",
             "Har ni en juniorgrupp",
             "Finns det någon barngrupp",
             "Har ni någon vuxengrupp",
             "Är det för barn eller vuxna",
             "Kan vuxna vara medlemmar",
             "Är ni uppdelade i barngrupp och vuxengrupp",
             "Barn under 13 år tränar för sig, och övriga tränar i "
             "vuxengruppen."]
        ]
        training_data = callcenter_training_data

        self.train(training_data)

    def train(self, training_data=None):

        if not training_data:
            training_data = self.training_data

        for data in training_data:
            intent_name = data[0]
            train_sentences = data[:-1]
            response_data = data[-1]

            intent = nlp.Intent(name=intent_name,
                                train_sentences=train_sentences,
                                response_data=response_data)
            self.all_intents.append(intent)

        self.parser = nlp.Parser(self.all_intents)

    def get_response(self, user_txt):
        response = ""

        if not len(user_txt):
            return "Vad ville du fråga?"

        user_txt = utils.unify_sentence_dividers(user_txt)
        sentences = utils.normalize_and_split_sentences(user_txt)

        for sentence in sentences:
            sentence = utils.remove_junk_chars(sentence)

            try:
                results = self.parser.parse(sentence)
                result = results[0]
                response += result.intent.response_data

            except IndexError:
                return "Tyvärr förstår jag inte din fråga."

        return response


if __name__ == "__main__":
    main()