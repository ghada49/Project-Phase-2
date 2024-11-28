import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QMessageBox, QScrollArea,QGridLayout, QDialogButtonBox,QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import socket

HOST = '127.0.0.1'
PORT = 12345
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

authenticated = False
current_user = None

#send_request take the data and transform it into json data. Then we receive a response from the server and transform it again
def send_request(data):
    json_data = json.dumps(data) # convert our data to json
    client_socket.sendall(json_data.encode('utf-8')) # we send the data to the client
    response = client_socket.recv(4096).decode('utf-8') # we receive our response from the server 
    
    try:
        response_data = json.loads(response) # we transform it again to return the data in our program
        return response_data
    except json.JSONDecodeError:
        print("Failed to decode JSON response from server.")
        return {}
    

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

        title = QLabel("Add Product")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.product_name = QLineEdit()
        self.product_name.setPlaceholderText("Enter product name")
        layout.addWidget(self.product_name)

        self.product_description = QLineEdit()
        self.product_description.setPlaceholderText("Enter product description")
        layout.addWidget(self.product_description)

        self.product_price = QLineEdit()
        self.product_price.setPlaceholderText("Enter product price")
        layout.addWidget(self.product_price)

        self.product_image = QLineEdit()
        self.product_image.setPlaceholderText("Enter image file path")
        layout.addWidget(self.product_image)
        
        self.product_quantity = QLineEdit()
        self.product_quantity.setPlaceholderText("Enter product quantity")
        layout.addWidget(self.product_quantity)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.add_product)
        layout.addWidget(submit_button)

        self.setLayout(layout)

    def add_product(self):
        product_name = self.product_name.text()
        product_description = self.product_description.text()
        product_price = self.product_price.text()
        product_image = self.product_image.text()
        product_quantity = self.product_quantity.text()
        if not product_name.strip() or not product_price.strip() or not product_description.strip() or not product_quantity.strip() or not product_image.strip() :
            QMessageBox.warning(self, "Input Error", "Please fill out all mandatory fields!")
            reply = QMessageBox.question(self, "Would you like to retry?", QMessageBox.Yes | QMessageBox.No,)
            if reply == QMessageBox.No:
                self.main_window.switch_to_main_app()
            else:
                QMessageBox.information(self, "Retry", "Please enter all required fields.")
        
        try:
            product_price = float(product_price)
            product_quantity = int(product_quantity)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid number for the price and quantity.")
            return
        command = { 
            "action": "ADD_PRODUCT",
            "product_name": product_name,
            "description": product_description,
            "price": product_price,
            "image_path": product_image, # image path is set to None if the user has not entered anything
            "quantity": product_quantity
    } # we store the data in command
        response = send_request(command)
        if "Image file not found" in response.get("message"):
            QMessageBox.warning(self, "Failed", response.get("message"))
            message=response.get("message")
            reply = QMessageBox.question(
                self,
                "Error in image",
                f"{message}\nWould you like retry?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.No:
                self.main_window.switch_to_main_app()

            else:
               QMessageBox.information(self, "Retry", "Please enter all required fields and image path correctly.")
        else:
            QMessageBox.information(self, "Success", response["message"])
            self.main_window.switch_to_main_app()

class ProductDetailsDialog(QDialog):
    '''"product_id": product[0],
            "product_name": product[1],
            "price": product[2],
            "short_description": product[3],
            "quantity": product[4],
            "image_path": product[5],
            "seller_info": product[6]'''
    def __init__(self, product):
        super().__init__()
        self.setWindowTitle(product.get("product_name"))
        self.setModal(True)
        self.setFixedSize(300, 400)

        layout = QVBoxLayout()

        # Product Name
        name_label = QLabel(product.get("product_name"))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(name_label)

        # Product Image
        image_label = QLabel()
        if product["image_path"]:
            pixmap = QPixmap(product["image_path"]).scaled(200, 200, Qt.KeepAspectRatio)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("No Image Available")
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

        # Product Price
        price_label = QLabel(f"Price: ${product.get('price', 0.0):.2f}")
        price_label.setAlignment(Qt.AlignCenter)
        price_label.setStyleSheet("font-size: 14px; color: green;")
        layout.addWidget(price_label)

        # Product Description
        description_label = QLabel(product.get("short_description"))
        description_label.setWordWrap(True)
        description_label.setStyleSheet("padding: 10px;")
        layout.addWidget(description_label)

        # Close Button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

class ViewProductAll(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout()

        title = QLabel("Available Products")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Scrollable area for products
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        list_container = QWidget()
        list_layout = QVBoxLayout()  # This layout will contain product buttons
        list_container.setLayout(list_layout)

        command = {"action": "VIEW_ALL_PRODUCTS"}
        response = send_request(command)

        if "No available products" in response.get("message"):
            QMessageBox.information(self, "No products", "We're sorry, no products available for sale.")
            self.main_window.switch_to_main_app()
            return
        else:
            products = response.get("products")
            if products:
                for product in products:
                    product_name_button = QPushButton(product.get("product_name"))

                    # Connect the product button to display product details
                    product_name_button.clicked.connect(lambda checked, p=product: self.show_product_details(p))
                    list_layout.addWidget(product_name_button)

                scroll_area.setWidget(list_container)
                layout.addWidget(scroll_area)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.main_window.switch_to_main_app)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def show_product_details(self, product):
        dialog = ProductDetailsDialog(product)
        dialog.exec_()

class ViewProduct(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.view_product_all_widget = None  # Initialize as None for lazy loading

        layout = QVBoxLayout()

        view_product_all_button = QPushButton("View All Products")
        view_product_all_button.clicked.connect(self.view_product_all)
        layout.addWidget(view_product_all_button)

        view_products_seller_button = QPushButton("View Products by Seller")
        view_products_seller_button.clicked.connect(self.view_product_seller)
        layout.addWidget(view_products_seller_button)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.go_back_main)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def view_product_all(self):
        if not self.view_product_all_widget:  # Create the widget only when accessed
            self.view_product_all_widget = ViewProductAll(self.main_window)
        self.main_window.stacked_widget.addWidget(self.view_product_all_widget)
        self.main_window.stacked_widget.setCurrentWidget(self.view_product_all_widget)

    def view_product_seller(self):
        self.main_window.switch_to_view_products_seller()

    def go_back_main(self):
        self.main_window.switch_to_main_app()

    

class MainAppScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout()

        self.username_label = QLabel("")
        self.username_label.setAlignment(Qt.AlignCenter)
        self.username_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.username_label)

        view_product_button = QPushButton("View Products")
        view_product_button.clicked.connect(self.view_product)
        layout.addWidget(view_product_button)

        add_product_button = QPushButton("Add Product")
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

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize all screens
        self.initial_screen = FirstScreen(self)
        self.login_form = Login(self)
        self.signup_form = Signup(self)
        self.main_app_screen = MainAppScreen(self)
        self.add_form = AddProduct(self)
        self.view_form = ViewProduct(self)
       # self.view_form_all = ViewProductAll(self)

        # Add widgets to the stack
        self.stacked_widget.addWidget(self.initial_screen)
        self.stacked_widget.addWidget(self.login_form)
        self.stacked_widget.addWidget(self.signup_form)
        self.stacked_widget.addWidget(self.main_app_screen)
        self.stacked_widget.addWidget(self.add_form)
        self.stacked_widget.addWidget(self.view_form)
        #self.stacked_widget.addWidget(self.view_form_all)

        # Set initial screen
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

    #def switch_to_view_products_all(self):
     #   self.stacked_widget.setCurrentWidget(self.view_form_all)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())