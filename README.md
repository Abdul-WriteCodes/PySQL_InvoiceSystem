INVOICE MANAGEMENT SYSTEM
The Invoice Management System is a Python-based application that helps businesses generate, store, and retrieve invoices using an SQLite database. This system is designed to be a simple, lightweight solution for managing invoicing operations, with capabilities for handling customer details, products purchased, and calculating totals (including VAT). The application operates through a command-line interface, making it easy to interact with and suitable for small to medium-sized businesses.

REQUIREMENTS
The system requires the following:
    1. Python 3.x: The main programming language used to develop the application.
    2. SQLite: A lightweight database used for storing invoice data. SQLite comes bundled with Python, so no additional installation is required.


WHAT THE APPLICATION DOES
1. Database Management
The system utilizes SQLite to manage and store invoice data. It automatically creates a database file (invoice_database.db) and ensures that the required table is available to store relevant information. This includes:
  1.  Company details (name, address, phone)
  2.  Customer details (name)
  3.  Itemized product details (product name, quantity, price, total amount)
  4.  The total amount (including VAT) for each invoice.

INVOICE GENERATION
Users can create new invoices by entering the following details:
  1. Customer Information: The name of the customer.
  2. Product Information: For each product purchased, the user will provide the product name, quantity, and unit price. The system will calculate the total amount for each item.
  3. VAT Calculation: The system automatically adds a predefined VAT to the total amount for the invoice.
  4. The invoice, along with all the relevant information, is then stored in the database with a unique invoice ID, which can be retrieved later.

INVOICE RETRIEVAL
Once an invoice is generated and stored in the database, users can retrieve it at any time by specifying the unique invoice ID. The system will display all the information related to that invoice, including the customer’s name, items purchased, and the total amount.


OPERATING PLATFORM
The application is operated through a simple and intuitive command-line interface. Users can interact with the system by selecting different options, including:
    [1] Generate a New Invoice: Allows users to input customer and product details and generate a new invoice.
    [2] Retrieve an Existing Invoice: Users can retrieve a previously generated invoice by its unique ID.
    [3] Exit: The user can exit the application at any time.



10
https://flutterwave.com/pay/j5m67hrqr4iq

25
https://flutterwave.com/pay/txyljcuqfsel


45
https://flutterwave.com/pay/yw7k3gmyjoud
