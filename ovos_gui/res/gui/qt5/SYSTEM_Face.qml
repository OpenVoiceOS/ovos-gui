import QtQuick.Layouts 1.4
import QtQuick 2.4
import QtQuick.Controls 2.0
import org.kde.kirigami 2.4 as Kirigami

import Mycroft 1.0 as Mycroft

Mycroft.CardDelegate {
    id: root

    contentItem: Face {
        // Set eyesOpen based on sessionData.sleeping
        eyesOpen: !sessionData.sleeping

        // Set mouth based on sessionData.sleeping
        mouth: sessionData.sleeping ? "GreySmile.svg" : "Smile.svg"
    }
    
}
