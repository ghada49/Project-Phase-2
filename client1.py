import sys
import json
import threading
import PyQt5
import traceback
import sys
import io
import os

from PyQt5.QtWidgets import (
    QApplication, QComboBox, QTextEdit, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QLineEdit, QMessageBox, QScrollArea,QGridLayout, QDialogButtonBox,QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import socket
import requests
from functools import partial
import difflib  
import google.generativeai as genai
genai.configure(api_key="AIzaSyDcadFbYXBg2jWgfq58UvveoQR0O8JWyoo")

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction="You are the AUBoutique Chatbot, designed to assist customers with frequently asked questions about AUBoutique. You can:\n\nRespond to inquiries about opening hours, location, and contact details.\nGuide sellers on how to register and list their products.\nProvide information about the types of products sold and the return policy.\nShare details about AUBoutique’s founders and background.\nIf customers ask about specific products, direct them to the \"Products/purchase\" section, where they can browse, search by seller, and explore product details. Always maintain a friendly and professional tone.\nYou can answer those questions : (of course you can reformulate the phrases and make them more firnedly but here are the answers and be welcoming to the maximum. Do not adopt to the same formulation of sentence. Be more dynamic and welcoming.)\n\"Good Evening\":\"Welcome to AUBoutique! I am AUBoutique Chatbot and I am here to answer frequently asked questions (general questions). How can I assist you today ?\",\n\"Good morning\":\"Welcome to AUBoutique! I am AUBoutique Chatbot and I am here to answer frequently asked questions (general questions). How can I assist you today ?\",\n\"hi\":\"Welcome to AUBoutique! I am AUBoutique Chatbot and I am here to answer frequently asked questions (general questions). How can I assist you today ?\",\n\"Hi\":\"Welcome to AUBoutique! I am AUBoutique Chatbot and I am here to answer frequently asked questions (general questions). How can I assist you today ?\",\n\"Hello!\":\"Welcome to AUBoutique! I am AUBoutique Chatbot and I am here to answer frequently asked questions (general questions). How can I assist you today ?\",\n\"When does AUBoutique open?\": \"AUBoutique is open on weekdays from 8 AM to 5 PM. It is closed on weekends.\",\n\"What is AUBoutique?\": \"AUBoutique is a platform where any seller can list their products for sale. It specializes in connecting buyers with unique, high-quality items.\",\n\"Can anyone sell on AUBoutique?\": \"Yes, AUBoutique allows any seller to register and add their products, provided they meet the platform's quality standards and guidelines.\",\n\"How can I register as a seller on AUBoutique?\": \"To register as a seller, visit our GUI, click on 'Sign up,' and fill out the application form with your details.\",\n\"What types of products are sold on AUBoutique?\": \"AUBoutique features a wide range of products, including fashion, accessories, home décor, electronics, food, and handmade goods.\",\n\"What do you sell?\":\"AUBoutique features a wide range of products, including fashion, accessories, home décor, electronics, food, and handmade goods.\",\n\"Is there a fee to sell on AUBoutique?\": \"AUBoutique does not charge any commission on products.\",\n\"Can I return products purchased on AUBoutique?\": \"Yes, products can be returned within 14 days after receival of products if they meet the return policy criteria, which vary by seller. You need to contact us at auboutique1@gmail.com.\",\n\"Does AUBoutique offer delivery services?\": \"No, AUBoutique does not provide delivery services. Buyers can pick up from our store in Hamra.\",\n\"How do I contact customer support for AUBoutique?\": \"You can contact AUBoutique's customer support through email: auboutique1@gmail.com.\",\n\"What is your email?\": \"You can contact AUBoutique's customer support through email: auboutique1@gmail.com.\",\n\"When can I come to AUBoutique?\": \"AUBoutique is open on weekdays from 8 AM to 5 PM. It is closed on weekends.\",\n\"Who are the founders of AUBoutique ?\": \"Ghada Al Danab, Aya El Hajj and Adam Hijazi founded AUBoutique. However, it is Dr. Ayman Kayssi who encouraged them to open this business.\",\n\"Can you give me information about such product?\":\"To see our products, you need to click on 'Products and Purchase' and you can find all the possible options/details there. AUBoutique is designed to answer frequently asked questions.\",\n\"Where is situated AUBoutique?\": \"Our boutique is situated in Beirut: Hamra, Bliss Street directly next to the coffee shop 'Stories'.\",\n\"How can I contact you ?\":\"You can contact AUBoutique's customer support through email: auboutique1@gmail.com.\",\n\"Where is the shop?\":\"Our boutique is situated in Beirut: Hamra, Bliss Street directly next to the coffee shop 'Stories'.\",\n\"Goodbye!\":\"Goodbye! Have a great week!\",\n\"See you!\":\"Goodbye! Have a great week!\".\n",
)



HOST = '127.0.0.1'
PORT = 12345
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

authenticated = False
current_user = None
chat_socket = None


#send_request take the data and transform it into json data. Then we receive a response from the server and transform it again
def send_request(data):
    try:
        json_data = json.dumps(data)
        client_socket.sendall(json_data.encode('utf-8'))
        response = client_socket.recv(8192).decode('utf-8')

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print("Failed to decode JSON response from server.")
            return {"message": "Invalid server response."}
    except ConnectionAbortedError as e:
        print(f"Connection aborted: {e}")
        return {"message": "Connection aborted by the server."}
    except Exception as e:
        print(f"Error during send_request: {e}")
        return {"message": "An error occurred while communicating with the server."}


def get_target_client_info(target_username):
    request_data = {"action": "GET_CLIENT_INFO", "target_username": target_username}
    response = send_request(request_data)

    if response.get("status") == "success":
        return response["ip"], response["port"]
    else:
        print(response.get("message"))
        return None, None



def initiate_chat(target_ip, target_port):
    global chat_socket
    chat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        chat_socket.connect((target_ip, target_port))
        print(f"Connected to {target_ip}:{target_port}")
        threading.Thread(target=receive_messages, args=(chat_socket,), daemon=True).start()
        threading.Thread(target=send_messages, args=(chat_socket,), daemon=True).start()
    except Exception as e:
        print(f"Could not connect to {target_ip}:{target_port} - {e}")




def receive_messages(chat_socket):
    while True:
        try:
            message = chat_socket.recv(1024).decode()
            if message:
                print(f"Received: {message}")
        except Exception as e:
            print(f"Error receiving message: {e}")
            break



def send_messages(chat_socket):
    while True:
        message = input("Enter message: ")
        try:
            chat_socket.send(message.encode())
        except Exception as e:
            print(f"Error sending message: {e}")
            break

def listen_for_p2p_connections():
    listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener_socket.bind((HOST, 0))  
    listener_socket.listen(1)
    ip, port = listener_socket.getsockname()

    print(f"P2P Listener started on {ip}:{port}")
    
    threading.Thread(target=accept_p2p_connections, args=(listener_socket,), daemon=True).start()
    return ip, port

def accept_p2p_connections(listener_socket):
    while True:
        conn, addr = listener_socket.accept()
        print(f"Incoming P2P connection from {addr}")
        threading.Thread(target=receive_messages, args=(conn,), daemon=True).start()



class ChatScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout()

        title = QLabel("Start P2P Chat")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username to chat with")
        layout.addWidget(self.username_input)

        chat_button = QPushButton("Start Chat")
        chat_button.clicked.connect(self.start_chat)
        layout.addWidget(chat_button)

        self.setLayout(layout)

    def start_chat(self):
        target_username = self.username_input.text()

        if not target_username:
            QMessageBox.warning(self, "Input Error", "Please enter a username.")
            return

        target_ip, target_port = get_target_client_info(target_username)

        if target_ip and target_port:
            initiate_chat(target_ip, target_port)
            self.main_window.switch_to_chat_screen()
        else:
            QMessageBox.warning(self, "Connection Error", "Could not find the target client.")


#The first screen with buttons to either log in or sign up
class FirstScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout()

        # Welcome Message
        title = QLabel("Welcome to the AUBoutique")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        # Buttons for Login and Sign Up
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.go_to_login)
        layout.addWidget(login_button)

        signup_button = QPushButton("Sign Up")
        signup_button.clicked.connect(self.go_to_signup)
        layout.addWidget(signup_button)

        self.setLayout(layout)

    def go_to_login(self):
        self.main_window.switch_to_login()

    def go_to_signup(self):
        self.main_window.switch_to_signup()


class Signup(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout()

        title = QLabel("Sign Up")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Name")
        layout.addWidget(self.name_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter Email")
        layout.addWidget(self.email_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        signup_button = QPushButton("Sign Up")
        signup_button.clicked.connect(self.signup)
        layout.addWidget(signup_button)

        self.setLayout(layout)

    def signup(self):
        name = self.name_input.text()
        email = self.email_input.text()
        username = self.username_input.text()
        password = self.password_input.text()

        command = {
            "action": "REGISTER",
            "name": name,
            "email": email,
            "username": username,
            "password": password,
        }
        response = send_request(command)

        if "Registration successful" in response.get("message"):
            QMessageBox.information(self, "Success", response["message"])
            self.main_window.switch_to_login()
        elif "already exists" in response.get("message").lower():
            self.handle_existing_user(response.get("message"))
        else:
            QMessageBox.warning(self, "Failed", response.get("message"))

    def handle_existing_user(self, message):
        #we give the user options to login or try to sign up again if username/email exists
        reply = QMessageBox.question(
            self,
            "Account Exists",
            f"{message}\nWould you like to log in instead?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.main_window.switch_to_login()
        else:
            QMessageBox.information(self, "Retry", "Please try signing up with a different username or email.")

class Login(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()

        title = QLabel("Login")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        ip, port = listen_for_p2p_connections()  # Start the listener

        command = {"action": "LOGIN", "username": username, "password": password, "p2p_port": port}
        response = send_request(command)

        if "Login successful" in response.get("message"):
            global authenticated, current_user
            authenticated = True
            current_user = username
            QMessageBox.information(self, "Success", response["message"])
            self.main_window.switch_to_main_app(username)
        else:
            QMessageBox.warning(self, "Failed", response.get("message"))

            reply = QMessageBox.question(
            self,"Account Exists", response.get("message") + "\nWould you like to sign up instead?",
            QMessageBox.Yes | QMessageBox.No,
        )
            if reply == QMessageBox.Yes:
                self.main_window.switch_to_signup()
            else:
                QMessageBox.information(self, "Retry", "Please enter correct username and password.")



class AddProduct(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout()

        # Title
        title = QLabel("Add Product")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        # Product Name
        self.product_name = QLineEdit()
        self.product_name.setPlaceholderText("Enter product name")
        layout.addWidget(self.product_name)

        # Product Description
        self.product_description = QLineEdit()
        self.product_description.setPlaceholderText("Enter product description")
        layout.addWidget(self.product_description)

        # Product Price with Unit
        price_layout = QHBoxLayout()

        self.product_price = QLineEdit()
        self.product_price.setPlaceholderText("Enter product price")
        price_layout.addWidget(self.product_price)

        self.price_unit = QComboBox()
        self.populate_currency_dropdown()  
        self.price_unit.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        price_layout.addWidget(self.price_unit)

        layout.addLayout(price_layout)

        # Product Image Path
        self.product_image = QLineEdit()
        self.product_image.setPlaceholderText("Enter image file path")
        layout.addWidget(self.product_image)

        # Product Quantity
        self.product_quantity = QLineEdit()
        self.product_quantity.setPlaceholderText("Enter product quantity")
        layout.addWidget(self.product_quantity)

        # Submit Button
        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.add_product)
        layout.addWidget(submit_button)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.go_back_main)
        layout.addWidget(back_button)
        self.setLayout(layout)

    def populate_currency_dropdown(self):
        """Populate the currency dropdown with common ISO 4217 currency codes."""
        currencies = ["USD", "EUR","LBP", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "SEK", "NZD"]
        for currency in currencies:
            self.price_unit.addItem(currency)

    def convert_currency(self, amount, from_currency):
        """Fetch conversion rate from an external API and convert the amount."""
        try:
            url = 'https://v6.exchangerate-api.com/v6/7d4c85f585fbd979f24c63d7/latest/USD'

            response = requests.get(url)
            data = response.json()

            rate_result = data['conversion_rates'][from_currency]
            return amount/rate_result
        except Exception as e:
            QMessageBox.warning(self, "Currency Conversion Error", f"An error occurred during conversion: {e}")
            return None

    def add_product(self):
        product_name = self.product_name.text()
        product_description = self.product_description.text()
        product_price = self.product_price.text()
        selected_currency = self.price_unit.currentText()
        product_image = self.product_image.text()
        product_quantity = self.product_quantity.text()

        if not all([product_name, product_description, product_price, product_image, product_quantity]):
            QMessageBox.warning(self, "Input Error", "Please fill out all mandatory fields!")
            return

        try:
            product_price = float(product_price)
            product_quantity = int(product_quantity)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numbers for price and quantity.")
            return

        converted_price = product_price
        if selected_currency != "USD":
            converted_price = self.convert_currency(product_price, selected_currency)
            if converted_price is None:  # If conversion fails, stop processing
                return
            QMessageBox.information(
                self, "Currency Converted", f"Price converted to USD: ${converted_price:.2f}"
            )

        command = {
            "action": "ADD_PRODUCT",
            "product_name": product_name,
            "description": product_description,
            "price": round(converted_price, 2), 
            "image_path": product_image,
            "quantity": product_quantity,
        }

        response = send_request(command)
        #response = self.send_request1(command) # hayda just for the display
        

        if response.get("message") == "Product added successfully.":
            QMessageBox.information(self, "Success", response.get("message"))
            self.main_window.switch_to_main_app()
        else:
            QMessageBox.warning(self, "Failed", "Error adding product. ")
    def go_back_main(self):
        self.main_window.switch_to_main_app()

   # def send_request1(self, command): 
    #    return {"status": "success", "message": "Product added successfully."}
class ViewCart(QWidget):
    def __init__(self, main_window, cart,selected_currency,exchange_rates):
        super().__init__()
        self.main_window = main_window
        self.cart = cart  # Cart passed from the main view
        self.selected_currency=selected_currency
        self.exchange_rates= exchange_rates

        layout = QVBoxLayout()

        title = QLabel("Your Cart")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_container.setLayout(self.list_layout)

        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)

        self.load_cart()

        checkout_button = QPushButton("Checkout")
        checkout_button.clicked.connect(self.checkout)
        layout.addWidget(checkout_button)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.main_window.switch_to_view_products)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def load_cart(self):
        """Load products in the cart."""
        for i in reversed(range(self.list_layout.count())):
            widget = self.list_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if not self.cart:
            QMessageBox.information(self, "Cart", "Your cart is empty.")
            return

        for product in self.cart:
            product_name = product.get("product_name")
            product_price = product.get("price", 0.0)
            product_id = product.get("product_id")

            product_widget = QHBoxLayout()
            if self.selected_currency=="USD":
                product_label = QLabel(f"{product_name} - ${product_price:.2f}")
                product_widget.addWidget(product_label)
            else:
                product_label = QLabel(f"{product_name} -- ${product_price:.2f} = {self.selected_currency} {self.convert_price(product_price)}")
                product_widget.addWidget(product_label)

            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(partial(self.remove_from_cart, product_id))
            product_widget.addWidget(remove_button)

            container = QWidget()
            container.setLayout(product_widget)
            self.list_layout.addWidget(container)

    def remove_from_cart(self, product_id):
        self.cart = [product for product in self.cart if product.get("product_id") != product_id]
        self.load_cart()
    def convert_price(self, amount):
        rate = self.exchange_rates[self.selected_currency]
        return round(amount * rate, 2)

    def checkout(self):
        """Checkout the cart."""
        if not self.cart:
            QMessageBox.information(self, "Checkout", "Your cart is empty.")
            return

        product_ids = [product.get("product_id") for product in self.cart]
        command = {"action": "PURCHASE", "product_id": product_ids}
        response = send_request(command)

        if response.get("message"):
            QMessageBox.information(self, "Purchase Successful", response.get("message"))
            self.cart.clear()
            self.load_cart()
        else:
            QMessageBox.warning(self, "Purchase Failed", "An error occurred during checkout.")
            
class ProductDetailsDialog(QDialog):
    def __init__(self, product, parent, selected_currency,exchange_rates):
        super().__init__()
        self.setWindowTitle(product.get("product_name"))
        self.setModal(True)
        self.resize(500, 700)
        self.parent = parent  
        self.selected_currency = selected_currency
        self.exchange_rates=exchange_rates
        self.setStyleSheet("""
            QDialog {
                background-color: #bbdefb;  
                border-radius: 10px;  
                color: #64b5f6;   
            }
            QLabel {
                color: #0F52BA;   
                font-size:20px;
                font-family: "Quicksand", sans-serif;
                
            }
            QPushButton {
                background-color: #90caf9;
                color: #0F52BA;   
                font-size:22px;
                font-weight:bold; 
                border: 2px solid #64b5f6;
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #64b5f6;
                color: white;   
                font-size:20px;
                font-weight:bold; 
                font-weight: bold;
            }
            QDialogButtonBox QPushButton {
                background-color: #90caf9; 
                color: #0F52BA;   
                font-size:20px;
                font-weight:bold; 
            }
            QLabel#titleLabel {
                color: #00008B;  
                font-size:20px;
            }
            QLabel#priceLabel {
                font-weight: bold;
                color: #0F52BA;  
                font-size:20px;
            }
            QLabel#descriptionLabel {
                color: #0F52BA;  
                font-size:20px;      
            }
        """)

        layout = QVBoxLayout()
        layout = QVBoxLayout()

        name_label = QLabel(product.get("product_name"))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 30px; font-weight: bold; color:#0F52BA;")
        layout.addWidget(name_label)

        image_label = QLabel()
        if product.get("image_path"):
            pixmap = QPixmap(product["image_path"]).scaled(400, 400, Qt.KeepAspectRatio)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("No Image Available")
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

        price_label = QLabel(f"Price: ${product.get('price', 0.0):.2f}")
        price_label.setAlignment(Qt.AlignCenter)
        price_label.setStyleSheet("font-size: 20px; color: #0F52BA;")
        layout.addWidget(price_label)
        if self.selected_currency!="USD":
            price_label2 = QLabel(f"Price: {self.selected_currency} {self.convert_price(product.get('price'))}")
            price_label2.setAlignment(Qt.AlignCenter)
            price_label2.setStyleSheet("font-size: 20px; color: #0F52BA; font-weight: bold;")
            layout.addWidget(price_label2)

        st = product.get("description", "No description available")
        description_label = QLabel(f"Description: {st}")
        description_label.setWordWrap(True)
        #description_label.setStyleSheet("padding: 12px;")
        layout.addWidget(description_label)

        quantity_label = QLabel(f"Quantity: {product.get('quantity', 0)}")
       # quantity_label.setAlignment(Qt.AlignCenter)
        quantity_label.setStyleSheet("font-size: 20px; color: #0F52BA;")
        layout.addWidget(quantity_label)

        avg_rating = self.get_average_rating(product.get("product_id"))
        rate_label = QLabel(f"Average Rating: {avg_rating}" if avg_rating else "No ratings yet")
        rate_label.setWordWrap(True)
        layout.addWidget(rate_label)


        add_cart_button = QPushButton("Add to Cart")
        add_cart_button.clicked.connect(partial(self.add_to_cart, product))
        layout.addWidget(add_cart_button)

        remove_cart_button = QPushButton("Remove from Cart")
        remove_cart_button.clicked.connect(partial(self.remove_from_cart, product))
        layout.addWidget(remove_cart_button)

        rate_label = QLabel("Rate this Product:")
        layout.addWidget(rate_label)

        self.rating_spinbox = QSpinBox()
        self.rating_spinbox.setRange(1, 5) 
        self.rating_spinbox.setStyleSheet("""
                background-color: white; 
                border: 2px solid #64b5f6; 
                border-radius: 8px; 
                color: #0F52BA; 
                font-weight: bold; 
                selection-background-color: #90caf9;
                height: 40px;
                width: 100px;
        """)

        layout.addWidget(self.rating_spinbox)

        rate_button = QPushButton("Submit Rating")
        rate_button.clicked.connect(partial(self.submit_rating, product))
        layout.addWidget(rate_button)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def add_to_cart(self, product):
        self.parent.cart.append(product)
        QMessageBox.information(self, "Added to Cart", f"{product.get('product_name')} has been added to your cart.")
    
    def convert_price(self, amount):
        rate = self.exchange_rates[self.selected_currency]
        return round(amount * rate, 2)

    def remove_from_cart(self, product):
        try:
            self.parent.cart.remove(product)
            QMessageBox.information(self, "Removed from Cart", f"{product.get('product_name')} has been removed from your cart.")
        except ValueError:
            QMessageBox.warning(self, "Not in Cart", f"{product.get('product_name')} is not in your cart.")


    def submit_rating(self, product):
        rating = self.rating_spinbox.value()  
        if not rating or rating < 1 or rating > 5:
            QMessageBox.warning(self, "Invalid Rating", "Please select a rating between 1 and 5.")
            return

        try:
            self.send_rating_to_server(product.get("product_id"), rating)
            QMessageBox.information(self, "Rating Submitted", f"Your rating of {rating} for {product.get('product_name')} has been submitted.")
        except Exception as e:
            print(f"Exception: {e}")
            traceback.print_exc()  # This will give you a full traceback
            QMessageBox.warning(self, "Server Error", f"Failed to submit rating: {str(e)}")

    def send_rating_to_server(self, product_id, rating):
        message = {
            "action": "RATE_PRODUCT",
            "product_id": product_id,
            "rating": rating
        }

        response = send_request(message)
        if response.get("status") == "success":
            print(f"Server response: {response.get('message')}")
        else:
            print(f"Server response: {response.get('message')}")

    def get_average_rating(self, product_id):
        response = send_request({
            "action": "GET_AVERAGE_RATING",
            "product_id": product_id
        })

        if response.get("status") == "success":
            return response.get("average_rating")
        else:
            return None


class ViewProductAll(QWidget):
    def __init__(self, main_window,selected_currency,exchange_rates):
        super().__init__()
        self.main_window = main_window
        self.cart = []
        self.selected_currency=selected_currency
        self.exchange_rates=exchange_rates
        layout = QVBoxLayout()


        title = QLabel("Available Products")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_container.setLayout(self.list_layout)

        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)

        command = {"action": "VIEW_ALL_PRODUCTS"}
        response = send_request(command)

        if "No available products" in response.get("message"):
            QMessageBox.information(self, "No Products", "We're sorry, no products available for sale.")
            back_button = QPushButton("Back")
            back_button.clicked.connect(self.main_window.switch_to_main_app)
            layout.addWidget(back_button)

            self.setLayout(layout)
            return

        products = response.get("products", [])
        for product in products:
            product_name_button = QPushButton(product.get("product_name"))
            product_name_button.clicked.connect(partial(self.show_product_details, product))
            self.list_layout.addWidget(product_name_button)

        checkout_button = QPushButton("Checkout")
        checkout_button.clicked.connect(self.checkout)
        layout.addWidget(checkout_button)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.main_window.switch_to_main_app)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def show_no_products(self, layout):
        """Display options when no products are available."""
        QMessageBox.information(self, "No Products", "We're sorry, no products available for sale.")
        self.main_window.switch_to_main_app()  # Redirect to main menu immediately

    def retry_view_products(self):
        """Retry fetching the products list."""
        self.main_window.switch_to_view_products()

    def show_product_details(self, product):
        dialog = ProductDetailsDialog(product, self,self.selected_currency,self.exchange_rates)
        dialog.exec_()
    

    def checkout(self):
        if not self.cart:
            QMessageBox.information(self, "No items in cart", "Your cart is empty.")
            return

        product_ids = [product.get("product_id") for product in self.cart]
        command = {"action": "PURCHASE", "product_id": product_ids}
        response = send_request(command)

        if response.get("message"):
            QMessageBox.information(self, "Purchase Successful", response.get("message"))
            self.cart.clear()
        else:
            QMessageBox.warning(self, "Purchase Failed", "An error occurred while processing your purchase.")

class ViewProductSeller(QWidget):
    def __init__(self, main_window,selected_currency,exchange_rates):
        super().__init__()
        self.main_window = main_window
        self.sellers = []
        self.cart = []
        self.selected_currency=selected_currency
        self.exchange_rates=exchange_rates
        layout = QVBoxLayout()

        title = QLabel("View Products by Seller")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        # Dropdown for seller selection
        self.seller_dropdown = QComboBox()
        self.seller_dropdown.setPlaceholderText("Select a Seller")
        self.populate_seller_dropdown()  # Populate the dropdown
        layout.addWidget(self.seller_dropdown)

        # Search button
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.get_products_by_seller)
        layout.addWidget(search_button)

         # Scroll area for displaying products
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_container.setLayout(self.list_layout)

        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)

        # Back button
        back_button = QPushButton("Back")
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def populate_seller_dropdown(self):
        """Populate the dropdown with available sellers."""
        command = {"action": "GET_SELLER_LIST"}
        try:
            response = send_request(command)  # Send the request to the server
            print(f"Server response: {response}")  # Debugging log

            if "Success" in response.get("message"):
                seller_list = response.get("sellers", [])
                if seller_list:
                    for seller in seller_list:
                        self.seller_dropdown.addItem(
                            f"{seller['username']} --- {seller['name']}", userData=seller['user_id']
                        )
                else:
                    self.seller_dropdown.addItem("No sellers available")
                    self.seller_dropdown.setDisabled(True)
            else:
                print("No sellers found or response issue.")  # Debugging 
                self.seller_dropdown.addItem("No sellers available")
                self.seller_dropdown.setDisabled(True)
        except Exception as e:
            print(f"Error populating seller dropdown: {e}")
            QMessageBox.warning(self, "Error", "Failed to fetch seller list.")


    def get_products_by_seller(self):
        seller_id = self.seller_dropdown.currentData()

        if not seller_id:
            QMessageBox.warning(self, "Selection Required", "Please select a seller from the dropdown.")
            return

        # Request to the server to fetch products by seller ID
        command = {"action": "VIEW_PRODUCTS_BY_SELLER", "seller_id": seller_id}
        response = send_request(command)
       # print(response) for debug
        # Clear previous results
        for i in reversed(range(self.list_layout.count())): 
            widget = self.list_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Handle response
        if "No products found" in response.get("message"):
            QMessageBox.information(self, "No Products", f"No products found for the selected seller.")
        else:
            products = response.get("products", [])
            for product in products:
                product_button = QPushButton(product.get("product_name"))
                product_button.clicked.connect(partial(self.show_product_details, product))
                self.list_layout.addWidget(product_button)

    def show_product_details(self, product):
        dialog = ProductDetailsDialog(product,self, self.selected_currency,self.exchange_rates)
        dialog.exec_()

    def go_back(self):
        self.main_window.switch_to_view_products(self.selected_currency)


class ViewProduct(QWidget):
    def __init__(self, main_window,selected_currency="USD"):
        super().__init__()
        self.main_window = main_window
        self.view_product_all_widget = None
        self.view_product_seller_widget = None
        self.search_product_widget = None
        self.selected_currency = selected_currency
        self.exchange_rates = {"USD":1}
        self.cart = []  # Initialize the cart here

        layout = QVBoxLayout()

        self.currency_label = QLabel(f"Currency selected: {self.selected_currency}")
        self.currency_label.setAlignment(Qt.AlignCenter)
        self.currency_label.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(self.currency_label)

        view_product_all_button = QPushButton("View All Products")
        view_product_all_button.clicked.connect(self.view_product_all)
        layout.addWidget(view_product_all_button)

        view_products_seller_button = QPushButton("View Products by Seller")
        view_products_seller_button.clicked.connect(self.view_product_seller)
        layout.addWidget(view_products_seller_button)

        search_product_button = QPushButton("Search Products by Name")
        search_product_button.clicked.connect(self.search_product_by_name)
        layout.addWidget(search_product_button)

        view_cart_button = QPushButton("View Cart")
        view_cart_button.clicked.connect(self.view_cart)
        layout.addWidget(view_cart_button)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.go_back_main)
        layout.addWidget(back_button)

        self.setLayout(layout)
        self.load_exchange_rates()  # Fetch exchange rates initially
        #self.load_products()
    
    def load_exchange_rates(self):
        try:
            url = 'https://v6.exchangerate-api.com/v6/7d4c85f585fbd979f24c63d7/latest/USD'
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTP errors
            data = response.json()

            if data.get('result') == 'success':
                self.exchange_rates = data.get('conversion_rates')
            else:
                raise Exception("Exchange rate API returned failure.")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch exchange rates: {e}")
            self.exchange_rates = {"USD": 1}  # Fallback to default

    def convert_price(self, amount):
        rate = self.exchange_rates[self.selected_currency]
        return round(amount * rate, 2)
    def view_product_all(self):
        #if not self.view_product_all_widget:
        self.view_product_all_widget = ViewProductAll(self.main_window,self.selected_currency,self.exchange_rates)
        self.view_product_all_widget.cart = self.cart  # Pass the cart
        self.main_window.stacked_widget.addWidget(self.view_product_all_widget)
        self.main_window.stacked_widget.setCurrentWidget(self.view_product_all_widget)

    def view_product_seller(self):
        if not self.view_product_seller_widget:
            self.view_product_seller_widget = ViewProductSeller(self.main_window,self.selected_currency,self.exchange_rates)
        self.view_product_seller_widget.cart = self.cart  # Pass the cart
        self.main_window.stacked_widget.addWidget(self.view_product_seller_widget)
        self.main_window.stacked_widget.setCurrentWidget(self.view_product_seller_widget)

    def search_product_by_name(self):
        if not self.search_product_widget:
            self.search_product_widget = SearchProductByName(self.main_window,self.selected_currency,self.exchange_rates)
        self.search_product_widget.cart = self.cart  # Pass the cart
        self.main_window.stacked_widget.addWidget(self.search_product_widget)
        self.main_window.stacked_widget.setCurrentWidget(self.search_product_widget)

    def view_cart(self):
        cart_widget = ViewCart(self.main_window, self.cart,self.selected_currency,self.exchange_rates)
        self.main_window.stacked_widget.addWidget(cart_widget)
        self.main_window.stacked_widget.setCurrentWidget(cart_widget)

    def go_back_main(self):
        self.main_window.switch_to_main_app()


class SearchProductByName(QWidget):
    def __init__(self, main_window,selected_currency,exchange_rates):
        super().__init__()
        self.main_window = main_window
        self.cart = []
        self.selected_currency= selected_currency
        self.exchange_rates=exchange_rates
        layout = QVBoxLayout()

        title = QLabel("Search Products by Name")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Input for product name
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter product name")
        layout.addWidget(self.search_input)

        # Search button
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search_product)
        layout.addWidget(search_button)

        # Scroll area to display results
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_container.setLayout(self.list_layout)

        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)

        # Back button
        back_button = QPushButton("Back")
        back_button.clicked.connect(self.main_window.switch_to_view_products)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def search_product(self):
        product_name = self.search_input.text()
        if not product_name.strip():
            QMessageBox.warning(self, "Input Error", "Please enter a product name.")
            return

        # Send search request to the server
        command = {"action": "SEARCH_PRODUCT_BY_NAME", "product_name": product_name}
        response = send_request(command)

        # Clear previous results
        for i in reversed(range(self.list_layout.count())):
            widget = self.list_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Handle response
        if "No products found" in response.get("message"):
            QMessageBox.information(self, "No Products", response.get("message"))
        else:
            products = response.get("products", [])
            for product in products:
                product_button = QPushButton(product.get("product_name"))
                product_button.clicked.connect(partial(self.show_product_details, product))
                self.list_layout.addWidget(product_button)

    def show_product_details(self, product):
        dialog = ProductDetailsDialog(product, self, self.selected_currency,self.exchange_rates)
        dialog.exec_()


class MainAppScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.selected_currency = "USD"  # Default currency

        layout = QVBoxLayout()

        self.username_label = QLabel("Welcome, {username}")
        self.username_label.setAlignment(Qt.AlignCenter)
        self.username_label.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(self.username_label)

        currency_layout = QHBoxLayout()

        currency_label = QLabel("Select Currency:")
        currency_label.setStyleSheet("font-size: 25px; font-weight: bold;")
        currency_layout.addWidget(currency_label)

        self.currency_dropdown = QComboBox()
        self.currency_dropdown.addItems(["USD", "EUR", "LBP", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "SEK", "NZD"])
        self.currency_dropdown.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: white; 
            background-color: #90caf9; 
            border-radius: 8px; 
            height: 35px; 
            width: 200px;
        """)
        currency_layout.addWidget(self.currency_dropdown)
        layout.addLayout(currency_layout)

        submit_currency_button = QPushButton("Submit Currency")
        submit_currency_button.clicked.connect(self.submit_currency)
        layout.addWidget(submit_currency_button)

        view_product_button = QPushButton("Products and Purchase")
        view_product_button.clicked.connect(self.view_product)
        layout.addWidget(view_product_button)

        add_product_button = QPushButton("Add Product to the Market")
        add_product_button.clicked.connect(self.add_product)
        layout.addWidget(add_product_button)

        ask_questions_chatbot=QPushButton("Ask questions to Chatbot")
        ask_questions_chatbot.clicked.connect(self.ask_questions)
        layout.addWidget(ask_questions_chatbot)

        start_chat_button = QPushButton("Start P2P Chat")
        start_chat_button.clicked.connect(self.start_chat)
        layout.addWidget(start_chat_button)

        logout_button = QPushButton("Logout")
        logout_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        logout_button.clicked.connect(self.logout)
        layout.addWidget(logout_button)

        self.setLayout(layout)
    
    def ask_questions(self):
        self.main_window.switch_to_ask_questions()

    def set_username(self, username):
        self.username_label.setText(f"Welcome, {username}")

    def submit_currency(self):
        self.selected_currency = self.currency_dropdown.currentText()
        QMessageBox.information(self, "Currency Updated", f"Currency set to {self.selected_currency}")

    def view_product(self):
        self.main_window.switch_to_view_products(self.selected_currency)

    def add_product(self):
        self.main_window.switch_to_add_products()

    def start_chat(self):
        self.main_window.switch_to_chat_screen()

    def logout(self):
        self.main_window.switch_to_initial()

class Chatbot(QWidget):
    def __init__(self,main_window):
        super().__init__()
        self.main_window = main_window
        self.chat_session = model.start_chat(history=[])
        self.setWindowTitle("AUBoutique Chatbot")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.chat_area = QTextEdit(self)
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            background-color: white;
            color: #0F52BA;
            border: 2px solid #64b5f6;
            border-radius: 8px;
            padding: 8px 18px;
            font-size: 20px;
            font-weight: 200;
        """)
        layout.addWidget(self.chat_area)

        self.input_field = QTextEdit(self)
        self.input_field.setFixedHeight(50)  
        self.input_field.setPlaceholderText("Write your question")
        self.input_field.setStyleSheet("""
            background-color: #64a1d6;
            color: white;
            border: 2px solid white;
            border-radius: 8px;
            padding: 8px 18px;
            font-size: 20px;
            font-weight: 500;
            height: 80px;
        """)
        layout.addWidget(self.input_field)

        self.send_button = QPushButton('Send', self)
        self.send_button.clicked.connect(self.handle_input)
        layout.addWidget(self.send_button)
        
        back_button = QPushButton("Back")
        back_button.clicked.connect(self.go_back_main)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def go_back_main(self):
        self.main_window.switch_to_main_app()

    #def add_message_user(self):
     #   user_input = self.input_field.toPlainText()
       # self.chat_area.append(f"You: {user_input}")


    def handle_input(self):
        user_input = self.input_field.toPlainText()
        self.input_field.clear()

        if user_input.lower() in ["exit", "quit"]:
            self.chat_area.append("Goodbye! Have a great day!")
            return

        response = self.chat_session.send_message(user_input)

        model_response = response.text
        
        self.chat_area.append(f"You: {user_input}")
        self.chat_area.append("---------------------------------------------------------------------------------------------------------------------")
        self.chat_area.append(f"AUBoutique Chatbot: {model_response}")
        self.chat_area.append("")  

        self.chat_session.history.append({"role": "user", "parts": [user_input]})
        self.chat_session.history.append({"role": "model", "parts": [model_response]})


class ChatScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.online_users = [] 

        layout = QVBoxLayout()

        # Title
        title = QLabel("Online Users")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: bold;")
        layout.addWidget(title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.users_container = QWidget()
        self.users_layout = QVBoxLayout()
        self.users_container.setLayout(self.users_layout)

        self.scroll_area.setWidget(self.users_container)
        layout.addWidget(self.scroll_area)

        button_layout = QHBoxLayout()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_online_users)
        button_layout.addWidget(refresh_button)

        back_button = QPushButton("Go Back")
        back_button.clicked.connect(self.go_back)
        button_layout.addWidget(back_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def refresh_online_users(self):
        command = {"action": "GET_ONLINE_USERS"}
        response = send_request(command)

        for i in reversed(range(self.users_layout.count())):
            widget = self.users_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if response.get("status") == "success":
            self.online_users = [ user for user in response.get("users", []) if user.get("username") != current_user]
            for user in self.online_users:
                user_button = QPushButton(user.get("username"))
                user_button.clicked.connect(partial(self.start_chat_with_user, user))
                self.users_layout.addWidget(user_button)
        else:
            QMessageBox.warning(self, "Error", response.get("message", "Failed to fetch online users."))

    def start_chat_with_user(self, user):
        target_username = user.get("username")
        target_ip, target_port = get_target_client_info(target_username)

        if target_ip and target_port:
            initiate_chat(target_ip, target_port)
            QMessageBox.information(self, "Chat Started", f"Connected with {target_username}.")
        else:
            QMessageBox.warning(self, "Error", f"Could not connect with {target_username}.")

    def go_back(self):
        self.main_window.switch_to_main_app()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUBoutique")
        self.setGeometry(200, 200, 900, 800)
        self.load_stylesheet("style.qss")

        # Initialize the QStackedWidget for switching between screens
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Create instances of all your screens
        self.initial_screen = FirstScreen(self)
        self.login_form = Login(self)
        self.signup_form = Signup(self)
        self.main_app_screen = MainAppScreen(self)
        self.add_form = AddProduct(self)
        self.view_form = None
        self.chatbot = Chatbot(self)
        self.chat_screen = ChatScreen(self)

        # Add all the screens to the stacked widget
        self.stacked_widget.addWidget(self.initial_screen)
        self.stacked_widget.addWidget(self.login_form)
        self.stacked_widget.addWidget(self.signup_form)
        self.stacked_widget.addWidget(self.main_app_screen)
        self.stacked_widget.addWidget(self.add_form)
        self.stacked_widget.addWidget(self.chatbot)
        self.stacked_widget.addWidget(self.chat_screen)

        # Set the initial screen
        self.stacked_widget.setCurrentWidget(self.initial_screen)

    def switch_to_login(self):
        self.stacked_widget.setCurrentWidget(self.login_form)

    def switch_to_signup(self):
        self.stacked_widget.setCurrentWidget(self.signup_form)

    def switch_to_main_app(self, username=None):
        if username:
            self.main_app_screen.set_username(username)
        self.stacked_widget.setCurrentWidget(self.main_app_screen)

    def switch_to_initial(self):
        self.stacked_widget.setCurrentWidget(self.initial_screen)

    def switch_to_add_products(self):
        self.stacked_widget.setCurrentWidget(self.add_form)

    def switch_to_view_products(self, selected_currency):
        if not self.view_form:
            self.view_form = ViewProduct(self, selected_currency)
            self.stacked_widget.addWidget(self.view_form)
        self.view_form.selected_currency = selected_currency
        self.stacked_widget.setCurrentWidget(self.view_form)

    def switch_to_ask_questions(self):
        self.stacked_widget.setCurrentWidget(self.chatbot)

    def load_stylesheet(self, filepath):
        try:
            with open(filepath, "r") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", f"Stylesheet file '{filepath}' not found.")

    def switch_to_chat_screen(self):
        self.stacked_widget.setCurrentWidget(self.chat_screen)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())