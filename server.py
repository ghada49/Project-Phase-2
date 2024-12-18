from email.message import EmailMessage
import json
import socket
import threading
import sqlite3
import database as db
from datetime import datetime, timedelta
import smtplib
import io



# Connect to SQLite3 database 'Boutique.db' but make sure to run the database.py file before inorder to create the database if it the first time you run
conn = sqlite3.connect('Boutique.db', check_same_thread=False)
cursor = conn.cursor()
db_lock = threading.Lock()

# server host and port to listen to incoming client connections
HOST = '127.0.0.1'
PORT = 12345
#dictionary to keep track of online users when they login and then remover from dictionary when logout
online_users = {}
message_queue = {}


def insert_rating(user_id, product_id, rating):
    try:
        rating_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Inserting rating: user_id={user_id}, product_id={product_id}, rating={rating}, date={rating_date}")
        cursor.execute("""
            INSERT INTO Ratings (user_id, product_id, rating, rating_date)
            VALUES (?, ?, ?, ?)
        """, (user_id, product_id, rating, rating_date))
        
        conn.commit()
        response = {
                        "status": "success",
                        "message":"Rating added successfully"
                    }
        return response
        
    except Exception as e:
        print("in except: ", e)
        response = {
                        "status": "failure",
                        "message": str(e),
                    }
        return response


def get_average_rating(product_id):
    cursor.execute('''
        SELECT AVG(rating) FROM Ratings
        WHERE product_id = ?
    ''', (product_id,))
    result = cursor.fetchone()
    if result[0] is not None:
        return result[0]
    else : return 0

#function to send email for buyer to confirm his/her purchase using smtp protocol
def send_email(recipient, productList, pickup_info):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'aub.boutique1@gmail.com' # this is the sender mail 
    sender_password = 'ljrb uhpe zbdr rcdb'
    
    products_formatted = "" # we compute the list of product bought into a string
    for i in range(len(productList)):
        products_formatted += str(i+1)+") "+productList[i] +'\n'
    subject = "Purchase Confirmation"
    body = f"""\
Dear customer,

Thank you for choosing AUBoutique! We are thrilled to confirm your recent purchase of 

{products_formatted}

Your order will be ready for pickup at the AUB Post Office on {pickup_info} between 9:00 am and 4:00 pm. If you have any questions or need assistance, feel free to reach out to us.

We look forward to serving you again in the future!

Best regards,
 
AUBoutique  

"""
# Here we are setting : the receiver mail, the subject and the content
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password) # we authenticate with our server mail 
            server.send_message(msg) # we send the message
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

def receive_req(client_socket):
    try:
        request = client_socket.recv(1024).decode('utf-8') # Receive request from the client
        if not request:
            return

        try:
            data = json.loads(request) #parse JSON data from the client request
        except json.JSONDecodeError:
            response = json.dumps({"error": "Invalid JSON format."})
            client_socket.send(response.encode('utf-8'))
            
    except:
        return


def handle_client(client_socket, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    authenticated_user = None
    global online_users

    try:
        while True:
            request = client_socket.recv(1024).decode('utf-8') # Receive request from the client
            if not request:
                break

            try:
                data = json.loads(request) #parse JSON data from the client request
            except json.JSONDecodeError:
                response = json.dumps({"error": "Invalid JSON format."})
                client_socket.send(response.encode('utf-8'))
                continue

            command = data.get("action") # extract the action specified in the request in order to know what to proceed with
             # Command to register a new user account by getting new: name, email, username, password from the client's request
            if command == "REGISTER":
                response = register_user(data.get("name"), data.get("email"), data.get("username"), data.get("password"))
                client_socket.send(json.dumps(response).encode('utf-8'))
             # Command to log in an existing user, updating online status if successful
            elif command == "LOGIN":
                response, authenticated_user = login_user(data.get("username"), data.get("password"))
                if authenticated_user:
                    online_users[authenticated_user[0]] = client_socket
                client_socket.send(json.dumps(response).encode('utf-8'))

            # Command to purchase a product by getting the product ID inputed by the client
            elif command == "PURCHASE" and authenticated_user:
                product_id = data.get("product_id")
                response = purchase_product(authenticated_user[0], product_id)
                client_socket.send(json.dumps(response).encode('utf-8'))

            # Command to add a new product listing to the marketplace
            elif command == "ADD_PRODUCT" and authenticated_user:
                response = add_product(authenticated_user[0], data.get("product_name"), data.get("description"), data.get("price"), data.get("quantity"), data.get("image_path"))
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to view all products listed by other sellers
            elif command == "VIEW_ALL_PRODUCTS" and authenticated_user:
                response = view_products(authenticated_user[0])
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to search for products listed by a specific seller
            elif command == "VIEW_PRODUCTS_BY_SELLER" and authenticated_user:
                response = search_products_by_seller(data.get("seller_id"))
                client_socket.send(json.dumps(response).encode('utf-8'))
            # Command to view the listing of the seller (products that he added that were sold or not)
            elif command == "VIEW_MY_LISTINGS" and authenticated_user:
                response = view_my_listings(authenticated_user[0])
                client_socket.send(json.dumps(response).encode('utf-8'))

            #Command to view the transactions (what we bought or sold)
            elif command == "VIEW_TRANSACTIONS" and authenticated_user:
                response = view_transactions(authenticated_user[0])
                client_socket.send(json.dumps(response).encode('utf-8'))
            elif command == "SEARCH_PRODUCT_BY_NAME" and authenticated_user:
                product_name = data.get("product_name", "")
                response = search_product_by_name(product_name)
                client_socket.send(json.dumps(response).encode('utf-8'))
           
            
            # Command to logout, we remove the user from being online 
            elif command == "LOGOUT" and authenticated_user:
                user_id = authenticated_user[0]
                cursor.execute("UPDATE Users SET status = 'Offline' WHERE user_id = ?", (user_id,))
                conn.commit()
                online_users.pop(user_id)
                client_socket.send(json.dumps({"message": "You have been logged out."}).encode('utf-8'))
            elif command == "RATE_PRODUCT" and authenticated_user:
                user_id = authenticated_user[0]
                
                product_id = data.get('product_id')
                rating = data.get('rating')
                
                if rating < 1 or rating > 5:
                    print("in if")
                    response = {"status": "failure", "message": "Rating must be between 1 and 5"}
                    client_socket.send(json.dumps(response).encode('utf-8'))
                    return
                print("Before response")
                response = insert_rating(user_id, product_id, rating)
                print("After response")
                client_socket.send(json.dumps(response).encode('utf-8'))
            elif command =="GET_AVERAGE_RATING" and authenticated_user:
                avg_rating = get_average_rating(data.get('product_id'))
                avg_rating = round(avg_rating, 1)

                response = {
                    "status": "success",
                    "message": f"Average rating for product {data.get('product_id')} fetched successfully.",
                    "average_rating": avg_rating
                }
                client_socket.send(json.dumps(response).encode('utf-8'))
            elif command=="GET_SELLER_LIST" and authenticated_user:
                print(f"Processing GET_SELLER_LIST for user: {authenticated_user[0]}")  # Debug log
                response = sellerlist()
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "FETCH_ONLINE_USERS" and authenticated_user:
                # Fetch all online users except the requester
                cursor.execute("SELECT username FROM Users WHERE status = 'Online' AND user_id != ?", (authenticated_user[0],))
                users = cursor.fetchall()
                online_users = [{"username": user[0]} for user in users] if users else []
                response = {"status": "success", "online_users": online_users}
                client_socket.send(json.dumps(response).encode('utf-8'))
            
            elif command == "SEND_MESSAGE" and authenticated_user:
                sender = authenticated_user
                recipient = data.get("recipient")
                message = data.get("message")
                
                if not recipient or not message:
                    response = {"status": "error", "message": "Recipient or message is missing."}
                    client_socket.send(json.dumps(response).encode('utf-8'))
                    return

                if recipient not in message_queue:
                    message_queue[recipient] = []
                
                message_queue[recipient].append({"sender": sender, "content": message})
                response = {"status": "success", "message": "Message sent."}
                client_socket.send(json.dumps(response).encode('utf-8'))

            elif command == "FETCH_MESSAGES" and authenticated_user:
                recipient = data.get("recipient")
                
                if not recipient:
                    response = {"status": "error", "message": "Recipient username is missing."}
                    client_socket.send(json.dumps(response).encode('utf-8'))
                    return

                if recipient in message_queue and message_queue[recipient]:
                    messages = message_queue[recipient]
                    message_queue[recipient] = [] 
                    response = {"status": "success", "messages": messages}
                else:
                    response = {"status": "success", "messages": []}  

                client_socket.send(json.dumps(response).encode('utf-8'))



    except Exception as e:
        response = {"status": "failure", "message": str(e)}
        client_socket.send(json.dumps(response).encode('utf-8'))

    except Exception as e:
        print(f"[ERROR] {e}")

    finally: # when the user exit, finally can run
        if authenticated_user:
            user_id = authenticated_user[0]
            cursor.execute("UPDATE Users SET status = 'Offline' WHERE user_id = ?", (user_id,)) # just in case, but this is not necessary since in logout we have already done that
            conn.commit()
            online_users.pop(user_id, None)
        client_socket.close()

# start_server() function sets up a server that listens to multiple clients at the same time

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # first, we are creating a new socket
    server.bind((HOST, PORT)) #binding it to the host and port
    server.listen() # the server listens for new connections 
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    while True: # so here, we have a "while true" which allows the server to continually accept new clients
        client_socket, addr = server.accept() #accepting connections
        thread = threading.Thread(target=handle_client, args=(client_socket, addr)) # new thread for each client
        thread.start() # we start the thread
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

# the register_user is used to create a new "account" in AUBoutique with the name, email, username, password provided from the client side
def register_user(name, email, username, password):
    with db_lock:
        try:
            cursor.execute(
                "INSERT INTO Users (name, email, username, password, status) VALUES (?, ?, ?, ?, 'Offline')",
                (name, email, username, password)
            ) 
            # we insert the fields mentionned above into the database so we have the account created and the user can log in with no problem
            conn.commit()
            return {"message": "Registration successful."}
        except sqlite3.IntegrityError:
            return {"message": "Username or email already exists."} 
            # if username or email is already in the database for another account an error is thrown and the user will have to register again
            
# the login_user helps to user to login. From client side, the user provides username and the password and send it to the server. When received, the server will make sure if these fields are in the database and if so, the user can login
def login_user(username, password):
    cursor.execute(
        "SELECT * FROM Users WHERE username = ? AND password = ?", (username, password)
    ) # so here we are searching for these credentials in the database to see if that account exists
    user = cursor.fetchone()
    if user: # if it does exist, then:
        cursor.execute(
            "UPDATE Users SET status = 'Online' WHERE username = ?", (username,)
        ) 
        # we set the user status to "Online" corresponding to the username of the user. Note that this is for the messaging option (we keep track of who is online and who is not when messaging)
        conn.commit()
        return {"message": "Login successful. Welcome to AUBoutique!"}, user
    return {"message": "Invalid credentials."}, None 
    # we will send a message saying credentials are wrong
# Note :
# in the server code, we send responses in this format: return {message : something}; when the client receive the message he will check the content at accordingly he will print, or prompt the user and so on so forth
# for example here : for invalid credentials: it will print it and the user will have to login again, so here it check what is the content of message and will act accordingly


# The add_product() function takes the inputs (product name, description, price and image path) of the user from the client side and then add them into the database to create a new product. The username of the one who added the product will be added as well.
def add_product(user_id, product_name, description, price,quantity, image_path):
    try:
    
        cursor.execute("""
            INSERT INTO Products (user_id, product_name, description, price, quantity, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, product_name, description, float(price),int(quantity), image_path))
        # as mentioned above, we are adding the characteristics mentioned above and we also have accounted an availibilty variable in the database to put if the product is available
        conn.commit()
        return {"message": "Product added successfully."}
    except:
        return {"message": "Product not added."}

# The view_products function shows all the products available 
def view_products(user_id):
    # Notice how here it is "Products.something" because we want to select all the products not only a specific one
    print("view in")
    cursor.execute("""
        SELECT 
            Products.product_id, 
            Products.product_name,
            Products.price,
            Products.description,
            Products.quantity,
            Products.image_path,
            Seller.username || ' - ' || Seller.name AS seller_info
        FROM 
            Products
        JOIN 
            Users AS Seller ON Products.user_id = Seller.user_id
        WHERE  
            Products.quantity != 0  
    """) 
# we only select available product

    products = cursor.fetchall()

    if not products: # if no products
        return {"message": "No available products found."}

    results = []
    for product in products:
        results.append({
            "product_id": product[0],
            "product_name": product[1],
            "price": product[2],
            "description": product[3],
            "quantity": product[4],
            "image_path": product[5],
            "seller_info": product[6]

        })
        # here we are appending all the information of products and note that it will be translated into a tabular form in the client side
    
    return {"message": "Product list below", "products": results}

#search_products_byseller has the same logic as view product except that we get from the user a specific seller (username) and view his product
def search_products_by_seller(user_id): 
    cursor.execute("""
        SELECT 
            Products.product_id,
            Products.product_name,
            Products.price,
            Products.description,
            Products.quantity,
            Products.image_path,
            Seller.username || ' - ' || Seller.name AS seller_info
        FROM 
            Products
        JOIN 
            Users AS Seller ON Products.user_id = Seller.user_id 
        WHERE 
            Seller.user_id = ? 
    """, (user_id,)) # note that here  we check the products of our wanted seller
    
    products = cursor.fetchall()

    if not products:
        return {"message": f"No products found for seller '{user_id}'."}

    results = []
    for product in products: #same as before
        results.append({
            "product_id": product[0],
            "product_name": product[1],
            "price": product[2],
            "description": product[3],
            "quantity": product[4],
            "image_path": product[5],
            "seller_info": product[6]
        })

    return {"message":f"Products for seller '{user_id}'." ,"products": results}
def search_product_by_name(product_name):
    try:
        cursor.execute('''
            SELECT 
                product_id, product_name, description, price, quantity, image_path 
            FROM Products
            WHERE product_name LIKE ?
        ''', (f"%{product_name}%",))  # Use LIKE for partial matches
        products = cursor.fetchall()

        if not products:
            return {"message": "No products found for the given name."}

        results = []
        for product in products:
            results.append({
                "product_id": product[0],
                "product_name": product[1],
                "description": product[2],
                "price": product[3],
                "quantity": product[4],
                "image_path": product[5],
            })

        return {"message": "Products found.", "products": results}
    except Exception as e:
        print(f"Error in search_product_by_name: {e}")
        return {"message": "An error occurred while searching for products."}
#The purchase function helps the user to select many products at the same time and purchase them
def purchase_product(buyer_id, product_ids):
    cursor.execute("SELECT email FROM Users WHERE user_id = ?", (buyer_id,))
    email_result = cursor.fetchone()
    
    emailToSend = email_result[0]  

    productNames = [] 
    for product_id in product_ids: # remember, product_ids is the list of ID of the products that we sent from the client side, so this list has the IDs of the products that the user wants
        cursor.execute(
            "SELECT product_name, quantity, user_id FROM Products WHERE product_id = ?", (product_id,)
        )
        product = cursor.fetchone() #we fetch to obtain the product
        if product: #if product is here
            product_name, quantity, seller_id = product  
            if seller_id == buyer_id: # a user is not allowed to buy his own product
                return {"message": "You cannot purchase your own product."}
            elif quantity >= 1:
                cursor.execute(
                    "UPDATE Products SET quantity = ? WHERE product_id = ?", (quantity-1,product_id,)
                ) 
                # Here we update from available to Sold since the product is bought
                conn.commit()
                transaction_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # the transaction time is set at this instant
                cursor.execute(
                    "INSERT INTO Transactions (buyer_id, product_id, transaction_date) VALUES (?, ?, ?)",
                    (buyer_id, product_id, transaction_date)
                ) # we add the transaction fields (buyer_id, product_id, transaction_date) into the table TRANSACTIONS

                conn.commit()
                productNames.append(product_name) # for each product we keep track of the name of the product and add it to our list which is an argument for the send email function since when sending a mail to the buyer we are also naming the products he bought  
                print(productNames)
        else:
            return {"message": f"Product ID {product_id} does not exist."} 
    
    if productNames:
        collection_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        send_email(emailToSend, productNames, collection_date) # here we send an email
        
        return {"message": f"Purchase successful! Please collect your product(s) from the AUB post office on {collection_date} between 9:00 am and 4:00 pm."}
    else :
        return {"message": f"No products selected"}


def view_my_listings(user_id):
    cursor.execute("""
        SELECT 
            Products.product_id,
            Products.product_name,
            Products.price,
            SUBSTR(Products.description, 1, 20) AS short_description,
            Products.status,
            CASE WHEN Products.image IS NOT NULL THEN 'Yes' ELSE 'No' END AS has_image
        FROM 
            Products
        WHERE 
            Products.user_id = ?
    """, (user_id,)) # here we are selecting those products that he has added 

    products = cursor.fetchall()

    if not products:
        return {"message": "You have no listings."}

    results = []
    for product in products:
        results.append({
            "product_id": product[0],
            "product_name": product[1],
            "price": product[2],
            "short_description": product[3],
            "status": product[4],
            "has_image": product[5]
        }) # and here is the information shown to the client side to the seller

    return {"message": "These are your listing: ","products": results}

# view transactions helps the user seller or buyer to see what he bought or sold and more details on that
def view_transactions(user_id):
    cursor.execute("""
        SELECT 
            Products.product_name,
            Products.price,
            Transactions.transaction_date,
            Buyer.username || ' - ' || Buyer.name AS buyer_info
        FROM 
            Transactions
        JOIN 
            Products ON Transactions.product_id = Products.product_id
        JOIN 
            Users AS Buyer ON Transactions.buyer_id = Buyer.user_id
        WHERE 
            Products.user_id = ?
        ORDER BY 
            Transactions.transaction_date DESC
    """, (user_id,))
    sold_transactions = cursor.fetchall() # here we are getting all the sold products 

    if not sold_transactions:
        sold_message ="No products sold."
    else:
        sold_message = "There are products sold"

    cursor.execute("""
        SELECT 
            Products.product_name,
            Products.price,
            Transactions.transaction_date,
            Seller.username || ' - ' || Seller.name AS seller_info
        FROM 
            Transactions
        JOIN 
            Products ON Transactions.product_id = Products.product_id
        JOIN 
            Users AS Seller ON Products.user_id = Seller.user_id
        WHERE 
            Transactions.buyer_id = ?
        ORDER BY 
            Transactions.transaction_date DESC
    """, (user_id,)) #Here all the bought products
    bought_transactions = cursor.fetchall()
    if not bought_transactions:
        bought_message ="No products bought."
    else:
        bought_message = "There are products bought"
     
    sold_results = []
    for trans in sold_transactions:
        sold_results.append({
            "product_name": trans[0],
            "price": trans[1],
            "transaction_date": trans[2],
            "buyer_info": trans[3]
        })

    bought_results = []
    for trans in bought_transactions:
        bought_results.append({
            "product_name": trans[0],
            "price": trans[1],
            "transaction_date": trans[2],
            "seller_info": trans[3]
        })

    return {"message":"sent", "bought_message": bought_message, "sold_message": sold_message,
        "sold_transactions": sold_results,
        "bought_transactions": bought_results
    }
def sellerlist():
    try:
        cursor.execute("SELECT DISTINCT user_id FROM Products")
        seller_ids = cursor.fetchall()  # Fetch all seller IDs

        if seller_ids:
            sellers = []
            for seller_id_tuple in seller_ids:
                seller_id = seller_id_tuple[0]

                # Fetch seller details
                cursor.execute("SELECT username, name FROM Users WHERE user_id=?", (seller_id,))
                seller_data = cursor.fetchone()

                if seller_data:
                    sellers.append({
                        'user_id': seller_id,
                        'username': seller_data[0],
                        'name': seller_data[1]
                    })

            return {"message": "Success", "sellers": sellers}
        else:
            return {"message": "No sellers found.", "sellers": []}
    except Exception as e:
        print(f"Error fetching seller list: {e}")
        return {"message": "Server error occurred.", "sellers": []}



if __name__ == "__main__":
    start_server()
