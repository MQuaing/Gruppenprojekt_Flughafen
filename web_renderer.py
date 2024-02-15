from web_server import web_server
import os
from flask import Flask, render_template, request
import util
from Database import Database
import inspect

class web_renderer(web_server):
    """
    Klasse für die Renderung von Webseiten basierend auf Vorlagen und Inhalten.

    Attributes:
    app (Flask): Die Flask-App für den Webrenderer.
    """
    app = None
    global db
    def __init__(self):
        """
        Initialisiert eine Instanz der Webrenderer-Klasse.
        Setzt die Flask-App auf die des zugrunde liegenden Web-Servers.
        """
        super().__init__()
        with Database() as db:
            db.delete_all_entries()
            db.set_entries("Ankunft", util.get_all(True))
            db.set_entries("Abflug", util.get_all(True))
        app = web_server.app
        
    def render_page(self, content_name, text=None):
        """
        Rendert eine HTML-Seite basierend auf Vorlagen und Inhalten.

        Args:
            content_name (str): Der Name des Inhalts, der gerendert werden soll.
            text (str, optional): Ein zusätzlicher Text, der in die Seite eingefügt werden soll.

        Returns:
            str: Der gerenderte HTML-Code für die Seite.
        """
        with open(
            f"{util.get_data_folder()}/templates/index.html", "r", encoding="utf8"
        ) as f:
            result = f.read()
        with open(
            f"{util.get_data_folder()}/templates/head.html", "r", encoding="utf8"
        ) as f:
            result = result.replace("$head$", f.read())

        with open(
            f"{util.get_data_folder()}/templates//nav.html", "r", encoding="utf8"
        ) as f:
            result = result.replace("$nav$", f.read())

        if os.path.exists(f"{util.get_data_folder()}/templates/{content_name}.html"):
            with open(
                f"{util.get_data_folder()}/templates/{content_name}.html",
                "r",
                encoding="utf8",
            ) as f:
                result = result.replace("$content$", f.read())
        else:
            result = result.replace("$content$", content_name)

        if text is not None:
            result = result.replace("$text$", text)
        db = Database()
        datenstand = str(db.get_datetime())
        with open(
            f"{util.get_data_folder()}/templates/foot.html", "r", encoding="utf8"
        ) as f:
            result = result.replace("$foot$", f.read().replace("$datenstand$", datenstand))

        return result
    
    @staticmethod
    def filter_data(data, param, filterred_data = {}, cnt =0 ):
        """
        Filtert Daten basierend auf einem Parameter und gibt die gefilterten Daten zurück.

        Args:
            data (dict): Ein Dictionary von Flugdaten.
            param (str): Der Parameter, nach dem gefiltert werden soll.
            filtered_data (dict, optional): Ein optionales Dictionary für die gefilterten Daten (default ist ein leeres Dictionary).
            cnt (int, optional): Ein Zähler für die Rekursion (default ist 0).

        Returns:
            dict: Ein Dictionary mit den gefilterten Flugdaten.
        """
        if cnt == len(data):
            return filterred_data
        for flugnummer, flugdaten in data.items():
                if flugnummer.lower() == param:
                    filterred_data.update({flugnummer: flugdaten})
                    continue
                for key in flugdaten["flugdaten"].keys():
                    try: #evtl try durch if ersetzen
                        if flugdaten["flugdaten"][key].lower() == param:
                            filterred_data.update({flugnummer: flugdaten})
                    except AttributeError:
                        pass
        return web_renderer.filter_data(data, param, filterred_data, cnt+1)
    
    @web_server.app.route("/ankunft")
    def ankunft(dataOnly=False):
        """
        Handler für die Ankunftsseite.

        Args:
            dataOnly (bool, optional): Ein Flag, das angibt, ob nur die Daten zurückgegeben werden sollen (default ist False).

        Returns:
            str: Die gerenderte HTML-Seite oder die Daten als JSON, abhängig vom dataOnly-Flag.
        """
        db = Database()
        if db.check_entries(inspect.stack()[0][3]) is True:
            db.delete_entries(inspect.stack()[0][3])
            db.set_entries(inspect.stack()[0][3], util.get_all(True))

        data = db.get_entries(inspect.stack()[0][3])

        sorted_data = dict(
            sorted(data.items(), key=lambda item: item[1]["flugdaten"]["abflugzeit"])
        )
        search_param = request.args.get("s")

        if search_param is not None:
            search_param = search_param.lower()
            filtered_data = dict()
            for flugnummer, flugdaten in sorted_data.items():
                if flugnummer.lower() == search_param:
                    filtered_data.update({flugnummer: flugdaten})
                    continue
                for key in flugdaten["flugdaten"].keys():
                    try:
                        if flugdaten["flugdaten"][key].lower() == search_param:
                            filtered_data.update({flugnummer: flugdaten})
                    except AttributeError:
                        pass

            if len(filtered_data) == 0:
                result = "Kein passender Flug gefunden"
            else:
                result = render_template("Flugplan.html", data=filtered_data, view="Ankünfte 🛬")
        else:
            result = render_template("Flugplan.html", data=sorted_data, view="Ankünfte 🛬")

        if dataOnly is True:
            return result
        return web_renderer.render_page(None, result)

    
    @web_server.app.route("/abflug")
    def abflug(dataOnly=False):
        """
        Handler für die Abflugseite.

        Args:
            dataOnly (bool, optional): Ein Flag, das angibt, ob nur die Daten zurückgegeben werden sollen (default ist False).

        Returns:
            str: Die gerenderte HTML-Seite oder die Daten als JSON, abhängig vom dataOnly-Flag.
        """
        #data = util.get_all()
        db = Database()
        if db.check_entries(inspect.stack()[0][3]) is True:
            db.delete_entries(inspect.stack()[0][3])
            db.set_entries(inspect.stack()[0][3], util.get_all(True))
    
        data = db.get_entries(inspect.stack()[0][3])

        sorted_data = dict(
            sorted(data.items(), key=lambda item: item[1]["flugdaten"]["abflugzeit"])
        )
        search_param = request.args.get("s")
        
        if search_param != None:
            search_param = search_param.lower()
            filterred_data = web_renderer.filter_data(sorted_data, search_param)
            
            if len(filterred_data) == 0: result = "Kein passender Flug gefunden"
            else: result = render_template("Flugplan.html", data=filterred_data, view="Abflüge 🛫")
        else: result = render_template("Flugplan.html", data=sorted_data, view="Abflüge 🛫")
        
        if dataOnly is True:
            return result
        return web_renderer.render_page(None, result)
        
    @web_server.app.route("/erweitert")
    def erweitert():
        return "todo"
    
        #@web_server.app.route('/<search_param>', methods=['GET', 'POST'])
    @web_server.app.route('/', methods=['GET'])
    def home():
        """
        Route für die Startseite des Webservers.

        Returns:
        str: Der gerenderte HTML-Code für die Startseite.
        """      
        
        return web_renderer.render_page(None, f"{web_renderer.ankunft(True)} {web_renderer.abflug(True)}")