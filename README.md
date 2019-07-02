![SAM LOGO](https://sam-dev.cs.hm.edu/uploads/-/system/appearance/logo/1/SAM_Logo_Text.png)

## What is this?

In diesem Ordner befindet sich die Objekterkennung.

Im Unterorder Python befindet sich der Pythonserver der Maßgeblich für die Erkennung zuständig ist.

![UML](https://sam-dev.cs.hm.edu/SAM-DEV/AADC/raw/yolov3/src/aadcUser/mlGuys/python/UML.png)

## Python

Das Herzstück dieses Ordners ist der PythonServer (python/objectDetectionServer.py).

Zubeginn werden der C++ Code, Gewichte, Config geladen.
Das Neuronalenetz wird gebaut.
Im Anschluss wartet der Server auf 3 Verbindungen.
Es werden 3 Thread gestartet. Jeder bekommt einen Socket.
Dieser Thread bekommt einen ping über das Netzwerk wenn der Client ein Bild fertig auf die Platte schreibt.
Nach dem das Bild durch das Neuronalenetz auf der Grafikarte leif werden die Detections noch bearbeitet.
So werden doppelte Detections gefiltert, Und die Id's umgemappt.
Die Erkannten Elemente werden zurück an den Client gesendet.
Die Antwort besteht darin erstmal einen Byte zu senden mit der Menge an Erkennungen.
Darauf hin werden für jede Erkennung ein Byte mit der Länge der Erkennung und der Erkennung selber gesendet.
Im Anschluss wartet der Thread auf ein neues Bild. Der Vorgang wiederholt sich.
Dies passiert aktuell auf 3 Threads. Die Anzahl kann man wahrscheinlich veringern.

## Filter

Der Filter empfängt das Bild von dem Fisheye indistortet.
Das erhaltene Bild wird auf das Filsystem geschrieben.
Durch einen Netzwerkping wird dem Pythonserver signalisiert dass, das Bild bereit steht.
Als Antwort bekommt der Filter die Detections. 
Diese werden geringfügig verarbeitet und auf den Outputpin geschrieben.

## Testing

Zum Testen des Pythonservers existiert die TestClient.py Datei.
Diese Startet den Server und wartet 20 Sekunden bis das Netz gebaut ist.
Danach werden Testbilder durch das Netz geschoben. Am Ende wird die Antwort überprüft.

## Ports

Die Ports:
PORT01 = 42425       The port used by the Client
PORT02 = 42426       Used by Client
PORT03 = 42427       Used by Client
PORT1 = 42422        The port used by the server
PORT2 = 42423        Used by Server
PORT3 = 42424        Used by Server

werden von dieser Komponente benötigt.

# TODO:

- Pythonserver soll direkt starten bei einem make aufruf.
- Überprüfung ob 3 Threads wirklich notwendig sind.
- Eventuel kann man sämtliche Berchnungen und Logik ins Pythonprogram zu verlagern.
- Neue weights mit einem neuen Datensatz trainieren. Unser Datensatz war sehr fehlerhaft.
- Distanzberechnung zu Object hinzufügen. => Markerdetector ersetzten.
- Automatisches starten des PythonServers