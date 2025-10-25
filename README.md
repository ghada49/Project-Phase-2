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

## 🧩 Libraries to Install  

Before running the project, install the following dependency:

```bash
pip install PyQt5
```

> **Note:** The following modules are part of Python’s **standard library** and usually **don’t require installation**:  
> `email`, `json`, `socket`, `threading`, `sqlite3`, `datetime`, `smtplib`

---

## 🖥️ How to Run  

### 1️⃣ Set up the environment  
Open **VS Code** and create a **virtual environment** inside the project folder containing `client.py` and `server.py`.

---

### 2️⃣ Initialize the database (first time only)  
Run the following command to create the `Boutique.db` file:

```bash
python database.py
```

---

### 3️⃣ Start the server  
```bash
python server.py
```

---

### 4️⃣ Start the client  
Open a **new terminal window**, navigate to the same folder, and run:

```bash
python client.py
```

You can open **multiple clients** in separate terminals to simulate multiple users.

---

## 🪟 GUI Overview  

### 🧾 Sign-Up / Login Section  

**Sign Up**
- Fill in: Name, Email, Username, Password  
- Click **Sign Up**

**Login**
- Enter **Username** and **Password**  
- Click **Login**

---

### 🏠 Main Window (After Authentication)  

- **Currency Selection** — Choose preferred currency and click **Submit Currency**  
- **Add Products** — Enter product details and click **Add Product**  
- **Browse Products** — View, search, or filter by seller  
- **Cart Management** — Add, remove, and checkout products  
- **Chat** — Message online users directly  
- **Chatbot** — Ask questions and receive automatic replies  
- **Logout** — Safely exit the application  

---

## 📦 Product Dialog Box  

Each product includes:
- Product name  
- Image  
- Price (USD and selected currency)  
- Average rating  
- Quantity available  

**Actions**
- Add to Cart  
- Remove from Cart  
- Rate Product  

---

📌 **Tip:** Keep the server running while using multiple clients to test messaging, rating, and product synchronization in real-time.


IMPORTANT NOTE:
Difference between python files having "1" and without it.
As mentioned in demo and report, we submitted two versions one with p2p chat and one with server/client
- client1.py / server1.py / style1.qss --> are for the version where chat is purely p2p
- client.py /server.py / style.qss --> are for the version where the chat is based on client/server interaction



