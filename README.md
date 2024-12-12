LIBRARIES TO INSTALL:

To run the code make sure that you install those libraries :

pip install pillow

Note that the following libraries below should be built-in in your Python so by default there is NO NEED to install them, but we will mention them here again if your version of python do not have them and if you get an error: pip install email
pip install json
pip install socket
pip install threading
pip install sqlite3
pip install datetime
pip install smtplib
pip install PyQt5


But again, in principle, those are built in and no need to install them. Please, first, try to run the code without them and if does not work, download the missing library.

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


2. Window After Login:
  - Select Currency (drop down) --> You need to select the currency, otherwise USD is default
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
	- Available user will be shown 
	- You press on the button containing the user's name to chat with them 
	If ame132 is online you will have [ ame132 button ] that you can click if you want to chat with her
  - Ask questions to Chatbot
	-You can ask any FAQ questions (mentioned in the report) and the chatbot will answer)


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

