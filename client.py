import sys
import json
import PyQt5
import traceback
import sys
import io
import os

from PyQt5.QtWidgets import (
    QApplication, QComboBox, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QLineEdit, QMessageBox, QScrollArea,QGridLayout, QDialogButtonBox,QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import socket
import requests
from functools import partial

HOST = '127.0.0.1'
PORT = 12345
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

authenticated = False
current_user = None


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

    

#The first screen with buttons to either log in or sign up
class FirstScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout()

        # Welcome Message
        title = QLabel("Welcome to the AUBoutique")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
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
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
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
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
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

        command = {"action": "LOGIN", "username": username, "password": password}
        response = send_request(command)

        if "Login successful" in response.get("message"):
            global authenticated, current_user
            authenticated = True # we keep track of it for later use 
            current_user = username  # we store the username here for later use 
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
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
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
    def __init__(self, main_window, cart):
        super().__init__()
        self.main_window = main_window
        self.cart = cart  # Cart passed from the main view

        layout = QVBoxLayout()

        title = QLabel("Your Cart")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
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

            product_label = QLabel(f"{product_name} - ${product_price:.2f}")
            product_widget.addWidget(product_label)

            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(partial(self.remove_from_cart, product_id))
            product_widget.addWidget(remove_button)

            container = QWidget()
            container.setLayout(product_widget)
            self.list_layout.addWidget(container)

    def remove_from_cart(self, product_id):
        """Remove a product from the cart."""
        self.cart = [product for product in self.cart if product.get("product_id") != product_id]
        self.load_cart()

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
    def __init__(self, product, parent):
        super().__init__()
        self.setWindowTitle(product.get("product_name"))
        self.setModal(True)
        self.setFixedSize(400, 600)
        self.parent = parent  
        self.setStyleSheet("""
            QDialog {
                background-color: #bbdefb;  
                border-radius: 10px;     
            }
            QLabel {
                color: #0d47a1;      
                font-family: "Quicksand", sans-serif;
            }
            QPushButton {
                background-color: #90caf9;
                color: white;
                border: 2px solid #64b5f6;
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 17px;
                font-weight: 500;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #64b5f6;
                color: white;
                font-weight: bold;
            }
            QDialogButtonBox QPushButton {
                background-color: #90caf9; 
                color: #2e4a62;
            }
            QLabel#titleLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2e4a62;          
            }
            QLabel#priceLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2e4a62;           
            }
            QLabel#descriptionLabel {
                font-size: 18px;
                color: #2e4a62;        
            }
        """)

        layout = QVBoxLayout()
        layout = QVBoxLayout()

        name_label = QLabel(product.get("product_name"))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(name_label)

        image_label = QLabel()
        if product.get("image_path"):
            pixmap = QPixmap(product["image_path"]).scaled(300, 300, Qt.KeepAspectRatio)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("No Image Available")
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

        price_label = QLabel(f"Price: ${product.get('price', 0.0):.2f}")
        price_label.setAlignment(Qt.AlignCenter)
        price_label.setStyleSheet("font-size: 14px; color: green;")
        layout.addWidget(price_label)
        st = product.get("description", "No description available")
        description_label = QLabel(f"Description: {st}")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("padding: 12px;")
        layout.addWidget(description_label)

        quantity_label = QLabel(f"Quantity: {product.get('quantity', 0)}")
       # quantity_label.setAlignment(Qt.AlignCenter)
        quantity_label.setStyleSheet("font-size: 14px; color: #0d47a1;")
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
        layout.addWidget(self.rating_spinbox)

        rate_button = QPushButton("Submit Rating")
        rate_button.clicked.connect(partial(self.submit_rating, product))
        layout.addWidget(rate_button)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def add_to_cart(self, product):
        if product not in self.parent.cart:
            self.parent.cart.append(product)
            QMessageBox.information(self, "Added to Cart", f"{product.get('product_name')} has been added to your cart.")
        else:
            QMessageBox.warning(self, "Already in Cart", f"{product.get('product_name')} is already in your cart.")

    def remove_from_cart(self, product):
        try:
            self.parent.cart.remove(product.get("product_id"))
            QMessageBox.information(self, "Removed from Cart", f"{product.get('product_name')} has been removed from your cart.")
        except ValueError:
            QMessageBox.warning(self, "Not in Cart", f"{product.get('product_name')} is not in your cart.")


    def submit_rating(self, product):
        rating = self.rating_spinbox.value()  
        print("rating= ", rating)
        if not rating or rating < 1 or rating > 5:
            QMessageBox.warning(self, "Invalid Rating", "Please select a rating between 1 and 5.")
            return

        try:
            print("sending to server")
            self.send_rating_to_server(product.get("product_id"), rating)
            print("sent to server")
            QMessageBox.information(self, "Rating Submitted", f"Your rating of {rating} for {product.get('product_name')} has been submitted.")
        except Exception as e:
            print("error from here")
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
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.cart = []
        layout = QVBoxLayout()

        title = QLabel("Available Products")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
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
            self.show_no_products(layout)  # Show the "No Products" state
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
        retry_button = QPushButton("Retry")
        retry_button.clicked.connect(self.retry_view_products)
        layout.addWidget(retry_button)

        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.main_window.switch_to_main_app)
        layout.addWidget(back_button)

    def retry_view_products(self):
        """Retry fetching the products list."""
        self.main_window.switch_to_view_products()

    def show_product_details(self, product):
        dialog = ProductDetailsDialog(product, self)
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
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.sellers = []
        self.cart = []
        layout = QVBoxLayout()

        title = QLabel("View Products by Seller")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
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
                print("No sellers found or response issue.")  # Debugging log
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
        print(response)
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
        dialog = ProductDetailsDialog(product, self)
        dialog.exec_()

    def go_back(self):
        self.main_window.switch_to_view_products()


class ViewProduct(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.view_product_all_widget = None
        self.view_product_seller_widget = None
        self.search_product_widget = None
        self.cart = []  # Initialize the cart here

        layout = QVBoxLayout()

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

    def view_product_all(self):
        if not self.view_product_all_widget:
            self.view_product_all_widget = ViewProductAll(self.main_window)
        self.view_product_all_widget.cart = self.cart  # Pass the cart
        self.main_window.stacked_widget.addWidget(self.view_product_all_widget)
        self.main_window.stacked_widget.setCurrentWidget(self.view_product_all_widget)

    def view_product_seller(self):
        if not self.view_product_seller_widget:
            self.view_product_seller_widget = ViewProductSeller(self.main_window)
        self.view_product_seller_widget.cart = self.cart  # Pass the cart
        self.main_window.stacked_widget.addWidget(self.view_product_seller_widget)
        self.main_window.stacked_widget.setCurrentWidget(self.view_product_seller_widget)

    def search_product_by_name(self):
        if not self.search_product_widget:
            self.search_product_widget = SearchProductByName(self.main_window)
        self.search_product_widget.cart = self.cart  # Pass the cart
        self.main_window.stacked_widget.addWidget(self.search_product_widget)
        self.main_window.stacked_widget.setCurrentWidget(self.search_product_widget)

    def view_cart(self):
        cart_widget = ViewCart(self.main_window, self.cart)
        self.main_window.stacked_widget.addWidget(cart_widget)
        self.main_window.stacked_widget.setCurrentWidget(cart_widget)

    def go_back_main(self):
        self.main_window.switch_to_main_app()


class SearchProductByName(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.cart = []
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
        dialog = ProductDetailsDialog(product, self)
        dialog.exec_()


class MainAppScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout()

        self.username_label = QLabel("Welcome, {username}")
        self.username_label.setAlignment(Qt.AlignCenter)
        self.username_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.username_label)

        # Buttons for various actions
        view_product_button = QPushButton("Products and Purchase")
        view_product_button.clicked.connect(self.view_product)
        layout.addWidget(view_product_button)

        add_product_button = QPushButton("Add Product to the Market")
        add_product_button.clicked.connect(self.add_product)
        layout.addWidget(add_product_button)

        logout_button = QPushButton("Logout")
        logout_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        logout_button.clicked.connect(self.logout)
        layout.addWidget(logout_button)

        self.setLayout(layout)

    def set_username(self, username):
        self.username_label.setText(f"Welcome, {username}")

    def add_product(self):
        self.main_window.switch_to_add_products()

    def view_product(self):
        self.main_window.switch_to_view_products()

    def logout(self):
        self.main_window.switch_to_initial()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUBoutique")
        self.setGeometry(100, 100, 600, 400)
        self.load_stylesheet("style.qss")
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)


        self.initial_screen = FirstScreen(self)
        self.login_form = Login(self)
        self.signup_form = Signup(self)
        self.main_app_screen = MainAppScreen(self)
        self.add_form = AddProduct(self)
        self.view_form = ViewProduct(self)


        self.stacked_widget.addWidget(self.initial_screen)
        self.stacked_widget.addWidget(self.login_form)
        self.stacked_widget.addWidget(self.signup_form)
        self.stacked_widget.addWidget(self.main_app_screen)
        self.stacked_widget.addWidget(self.add_form)
        self.stacked_widget.addWidget(self.view_form)


        self.stacked_widget.setCurrentWidget(self.initial_screen)

    def switch_to_login(self):
        self.stacked_widget.setCurrentWidget(self.login_form)

    def switch_to_signup(self):
        self.stacked_widget.setCurrentWidget(self.signup_form)

    def switch_to_main_app(self, username=None):
        if username:  # Set username for the main app screen
            self.main_app_screen.set_username(username)
        self.stacked_widget.setCurrentWidget(self.main_app_screen)

    def switch_to_initial(self):
        self.stacked_widget.setCurrentWidget(self.initial_screen)

    def switch_to_add_products(self):
        self.stacked_widget.setCurrentWidget(self.add_form)

    def switch_to_view_products(self):
        self.stacked_widget.setCurrentWidget(self.view_form)

    def load_stylesheet(self, filepath):
        try:
            with open(filepath, "r") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", f"Stylesheet file '{filepath}' not found.")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())