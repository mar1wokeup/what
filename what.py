import sys
import os
import uuid
import base64

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QLabel, QVBoxLayout, QFileDialog, QSystemTrayIcon, QMenu, QAction, QShortcut
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QGuiApplication, QScreen, QIcon, QKeySequence

import requests
import json
import threading

from openai import OpenAI

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

class SelectionBox(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setGeometry(0, 0, 1680, 1050)

        self.pen = QPen(QColor(0, 255, 0), 2, Qt.DotLine)
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_selecting = False
        self.selection_made = False

    def mousePressEvent(self, event):
        if not self.selection_made:
            self.start_point = event.pos()
            self.end_point = self.start_point
            self.is_selecting = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.is_selecting = False
        self.selection_made = True
        self.update()

    def paintEvent(self, event):
        if self.is_selecting or self.selection_made:
            painter = QPainter(self)
            painter.setPen(self.pen)
            rect = QRect(self.start_point, self.end_point)
            self.selected_rect = rect.normalized()
            painter.drawRect(self.selected_rect)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

class ScreenCaptureApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setGeometry(0, 0, 1680, 1050)
        self.setWindowTitle('GPT-4 Vision Query Tool')

        # Layout
        layout = QVBoxLayout()

        # Button for screen capture
        self.btn_capture = QPushButton('Capture Screen Area', self)
        self.btn_capture.clicked.connect(self.captureScreen)
        layout.addWidget(self.btn_capture)


        # Text input for user query
        self.query_input = QLineEdit(self)
        layout.addWidget(self.query_input)

        # Button to send request
        self.btn_send = QPushButton('Send Request', self)
        self.btn_send.clicked.connect(self.sendRequest)
        layout.addWidget(self.btn_send)

        # Label for response
        self.response_label = QLabel(self)
        layout.addWidget(self.response_label)

        self.setLayout(layout)

        # System Tray Icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('path_to_icon.png'))  # Set your icon path
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.shortcut = QShortcut(QKeySequence("Ctrl+Shift+X"), self)
        self.shortcut.activated.connect(self.captureScreen)

    def captureScreen(self):
        # Logic for screen capture
        self.hide()  # Hide the window temporarily
        self.selection_box = SelectionBox()
        self.selection_box.show()

        # filename, _ = QFileDialog.getSaveFileName(self, "Capture", "", "PNG Files (*.png)")
        # if filename:
        #     pixmap = QApplication.primaryScreen().grabWindow(0)
        #     rect = self.getSelectionRect()
        #     if rect:
        #         cropped = pixmap.copy(rect)
        #         cropped.save(filename, "PNG")
        #         self.screenshot_path = filename

        self.selection_box.closeEvent = self.onSelectionBoxClosed
    
    def onSelectionBoxClosed(self, event):
        if hasattr(self.selection_box, 'selected_rect'):
            screen = QGuiApplication.primaryScreen()
            screenshot = screen.grabWindow(0, 
                                           self.selection_box.selected_rect.x(), 
                                           self.selection_box.selected_rect.y(), 
                                           self.selection_box.selected_rect.width(), 
                                           self.selection_box.selected_rect.height())
            self.screenshot_path = self.saveScreenshot(screenshot)  # Set the screenshot_path here
            print(f"Screenshot saved at {self.screenshot_path}")  # For debugging
            self.show()

    def saveScreenshot(self, pixmap):
        folder = 'screens'
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = os.path.join(folder, f"{uuid.uuid4()}.png")
        pixmap.save(filename, "PNG")
        return filename

    def getSelectionRect(self):
        # Implement logic for user to select a screen area
        # For simplicity, this is not implemented in this example
        return QRect(100, 100, 300, 200) # Placeholder rectangle

    def sendRequest(self):
        # Logic to send request to GPT-4 Vision API
        # This is a placeholder as the actual API details may vary
        client = OpenAI(api_key="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")

        # response = client.completions.create(
        #   model="gpt-4-vision-preview",
        #   prompt=self.query_input.text(),
        #   image=self.screenshot_path,
        #   temperature=1,
        #   max_tokens=256,
        #   top_p=1,
        #   frequency_penalty=0,
        #   presence_penalty=0
        # )

        #encode image
        self.encoded_image = encode_image(self.screenshot_path)

        response = client.chat.completions.create(
          model="gpt-4-vision-preview",
          messages=[
            {
              "role": "user",
              "content": [
                {"type": "text", "text": self.query_input.text()},
                {
                  "type": "image_url",
                  "image_url": {
                    "url": f"data:image/jpeg;base64,{self.encoded_image}",
                  },
                },
              ],
            }
          ],
          max_tokens=200,
        )


        # api_url = "https://api.openai.com/v1/gpt-4-vision"
        # headers = {"Authorization": "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"}
        # data = {
        #     "image": self.screenshot_path,
        #     "query": self.query_input.text()
        # }
        # response = requests.post(api_url, headers=headers, data=data)
        self.displayResponse(response.json())
        #self.displayResponse({"error": "API request failed"})



    def displayResponse(self, response):
        if not hasattr(self, 'response_overlay'):
            self.response_overlay = ResponseOverlay(self)

        response_text = json.dumps(response, indent=4)  # Format the response as text
        self.response_overlay.displayResponse(response_text)

    # def setupKeyboardShortcut(self):
    #     # Setup a global keyboard shortcut
    #     keyboard.add_hotkey('ctrl+shift+x', self.showFromShortcut)

    def showFromShortcut(self):
        # Show the app window from keyboard shortcut
        self.show()
        self.activateWindow()  # Brings the window to the front

class ResponseOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 400, 300)  # Adjust size and position as needed

        layout = QVBoxLayout(self)

        self.response_label = QLabel(self)
        layout.addWidget(self.response_label)

        self.setLayout(layout)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def displayResponse(self, response_text):
        self.response_label.setText(response_text)
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ScreenCaptureApp()
    ex.show()
    # threading.Thread(target=ex.setupKeyboardShortcut, daemon=True).start()
    sys.exit(app.exec_())