# 🛍️ AUB Boutique  

AUB Boutique is a **client–server online marketplace** designed for buyers and sellers within the AUB community.  
It enables users to register, log in securely, add and purchase products, chat with others, and interact with a built-in chatbot — all through a GUI-based Python application.

---

## ⚙️ Features  

### 👤 User Authentication  
- **Sign Up:** Create a new account by entering your name, email, username, and password.  
- **Login:** Securely log in using your username and password.  

### 💱 Currency Selection  
- Users can select their preferred currency (USD by default).  
- Automatic price conversion and display in the chosen currency.  

### 🛒 Marketplace Functionality  
- **Add Products:**  
  - Input product name, description, image path, price, currency, and quantity.  
  - Click “Add Product” to publish your listing.  
- **View All Products:**  
  - Display products in organized widgets.  
  - Click on a product to view detailed information.  
- **Search Products:**  
  - Use the search bar to find items by name.  
- **Filter by Seller:**  
  - Select a seller from a dropdown to view their products.  
- **Shopping Cart:**  
  - Add or remove products, view total prices, and proceed to checkout.  

### 💬 Communication  
- **Live Chat:**  
  - View online users and click on a username to start a chat.  
- **Chatbot:**  
  - Ask frequently asked questions (FAQs) and get automated responses.

### ⭐ Product Ratings  
- Users can rate purchased products, and average ratings appear in product details.  

### 🚪 Logout  
- Log out safely when done using the application.  


IMPORTANT NOTE:
Difference between python files having "1" and without it.
As mentioned in demo and report, we submitted two versions one with p2p chat and one with server/client
- client1.py / server1.py / style1.qss --> are for the version where chat is purely p2p
- client.py /server.py / style.qss --> are for the version where the chat is based on client/server interaction

LIBRARIES TO INSTALL:

To run the code make sure that you install those libraries :

pip install email
pip install json
pip install socket
pip install threading
pip install sqlite3
pip install datetime
pip install smtplib
pip install PyQt5


HOW TO RUN THE CODE:

First make sure to create an environment using VS Code for the folder the (client.py and server.py exist)
Run the database.py file in order to create the database (Boutique.db) if it is the first time and database still doesn't exist
Use the cd command to change directories. For example, if your file is in C:\Users\YourUsername\Documents do cd C:\Users\YourUsername\Documents
Then, run the server (python server.py)
Then open another command and do the same with the directories. Run client.py (you can open different commands to run multiple clients)
MAIN STRUCTURE OF THE GUI : (More details in the demo)

1. Sign-Up / Login Section:
- Sign Up: Click on the button then -->
	In sign up, You will need to fill:
		- Name
		- Email
		- Username
		- Password
           [ Sign up button ] --> we click it after filling it
- Login
	In login, You will need to fill
		- Username
		- Password
	[ Login button ] --> we click it after filling it


2. Window After Login (after authentication):
  - Select Currency (drop down) --> You can select the currency, otherwise USD is default
  - Submit Currency
  - Add Products 
	In add products, you need to fill :
		- Name
		- Description
		- Image path if you want to add image
		- Price with its currency
		- Quantity 
         [ Add product button ] --> we click this after filling those fields 

  - Products and Purchase (detailed below)
  - Start Chatting (with users)
	- Online user will be shown 
	- You press on the button containing the user's name to chat with them 
	If ame132 is online you will have [ ame132 button ] that you can click if you want to chat with her
  - Ask questions to Chatbot
	-You can ask any FAQ questions (mentioned in the report) and the chatbot will answer)
  - Logout:
    logout application when done 


3. Products and purchase:
  - View All Products
	- The name of the products will appear and each product is in a widget
	- When you click on the Widget you will get the Product Dialog Box infos (detailed below)
	- There is also the checkout button when you have added all the product that you wante
  - Search Product
	- There is a search bar to write the name of the wanted product and then press on the search button
  - View by Seller
	- You select in the dropdown the seller and see his/her products
  - View Cart
	- You can view the items that you added to your cart (their name + price) and you have the option to remove them if you want


4. Product Dialog Box:
  - You will have in this box : the name of the product, the image, the price in dollars and in the currency that you chose if you did, average rating if it has been rated, quantity.
You can also :
  - Add to Cart
  - Remove from Cart
  - Rate Product

