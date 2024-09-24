import random
import sys
import bcrypt
from pymongo import MongoClient

class Bank:
    def __init__(self):
        # MongoDB connection setup
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['BankDB']
        self.accounts = self.db['accounts']
        self.transactions = self.db['transactions']

    def hash_password(self, password):
        """Hashes the password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password

    def check_password(self, stored_password, entered_password):
        """Verifies the entered password with the stored hashed password."""
        return bcrypt.checkpw(entered_password.encode('utf-8'), stored_password)

    def create_account(self, first_name, last_name, mobile_num, aadhaar_num, password):
        """Creates a new account."""
        try:
            # Validate inputs
            if len(str(mobile_num)) != 10 or len(str(aadhaar_num)) != 12:
                raise ValueError("Invalid mobile or Aadhaar number")

            account_number = random.randint(100000000000, 999999999999)
            customer_name = f"{first_name} {last_name}"

            # Hash the password
            hashed_password = self.hash_password(password)

            account_data = {
                "account_number": account_number,
                "customer_name": customer_name,
                "mobile_num": mobile_num,
                "aadhaar_num": aadhaar_num,
                "balance": 0,
                "password": hashed_password  # Storing the hashed password
            }

            # Insert account into MongoDB
            result = self.accounts.insert_one(account_data)

            if result.inserted_id:
                print(f"Account created successfully. Your account number is {account_number}")
            else:
                print("Account creation failed. Please try again.")
        except Exception as e:
            print(f"Error: {e}")

    def authenticate(self, account_number, password):
        """Authenticates the user by verifying the password."""
        account = self.accounts.find_one({"account_number": account_number})
        if not account:
            raise ValueError("Account not found")
        
        # Check if the entered password matches the stored hashed password
        if not self.check_password(account['password'], password):
            raise ValueError("Incorrect password")
        
        print("Authentication successful")
        return True

    def deposit(self, account_number, amount):
        """Deposits an amount into the account."""
        try:
            if amount <= 0:
                raise ValueError("Deposit amount must be positive")

            # Find the account and update the balance
            result = self.accounts.find_one_and_update(
                {"account_number": account_number},
                {"$inc": {"balance": amount}},
                return_document=True
            )

            if result:
                print(f"Deposit successful. New balance is {result['balance']}")
            else:
                print("Account not found.")
        except Exception as e:
            print(f"Error: {e}")

    def withdraw(self, account_number, amount, password):
        """Withdraws an amount from the account after password authentication."""
        try:
            # Authenticate user
            self.authenticate(account_number, password)

            if amount <= 0:
                raise ValueError("Withdrawal amount must be positive")

            account = self.accounts.find_one({"account_number": account_number})

            if not account:
                raise ValueError("Account not found")

            if account['balance'] < amount:
                raise ValueError("Insufficient funds")

            # Update balance
            self.accounts.update_one({"account_number": account_number}, {"$inc": {"balance": -amount}})
            print(f"Withdrawal successful. New balance is {account['balance'] - amount}")
        except Exception as e:
            print(f"Error: {e}")

    def transfer(self, from_account, to_account, amount, password):
        """Transfers amount from one account to another after password authentication."""
        try:
            # Authenticate user
            self.authenticate(from_account, password)

            if from_account == to_account:
                raise ValueError("Cannot transfer to the same account")
            if amount <= 0:
                raise ValueError("Transfer amount must be positive")

            sender = self.accounts.find_one({"account_number": from_account})
            receiver = self.accounts.find_one({"account_number": to_account})

            if not sender or not receiver:
                raise ValueError("Invalid account numbers")

            if sender['balance'] < amount:
                raise ValueError("Sender has insufficient balance")

            # Perform the transfer
            self.withdraw(from_account, amount, password)
            self.deposit(to_account, amount)
            print(f"Transfer of {amount} from account {from_account} to account {to_account} successful.")
            print(f"Your new balance is {sender['balance'] - amount}.")  # Show only sender's balance
        except Exception as e:
            print(f"Error: {e}")

    def check_balance(self, account_number):
        """Checks the balance of the account."""
        try:
            account = self.accounts.find_one({"account_number": account_number})
            if not account:
                raise ValueError("Account not found")

            print(f"Account balance is: {account['balance']}")
            return account['balance']
        except Exception as e:
            print(f"Error: {e}")
            return None

    def delete_account(self, account_number, password):
        """Deletes an account after password authentication."""
        try:
            # Authenticate user
            self.authenticate(account_number, password)

            result = self.accounts.delete_one({"account_number": account_number})
            if result.deleted_count == 1:
                print(f"Account {account_number} deleted successfully.")
            else:
                print("Account deletion failed.")
        except Exception as e:
            print(f"Error: {e}")

# Main Function
def main():
    bank = Bank()
    while True:
        print("\n***Welcome To OnlineBanking***")
        print("1. Existing Customer")
        print("2. New Customer")
        print("3. Exit")
        choice = input("Enter your choice: ")

        try:
            if choice == '1':
                account_number = int(input("Enter your Account Number: "))
                password = input("Enter your password: ")  # Prompt for password
                
                while True:
                    print("\n1. Deposit\n2. Withdraw\n3. Balance Enquiry\n4. Transfer Funds\n5. Delete Account\n6. Back to Main Menu")
                    choice2 = input("Enter your choice: ")

                    if choice2 == '1':
                        amount = float(input("Enter amount to deposit: "))
                        bank.deposit(account_number, amount)
                    elif choice2 == '2':
                        amount = float(input("Enter amount to withdraw: "))
                        bank.withdraw(account_number, amount, password)  # Pass password
                    elif choice2 == '3':
                        bank.check_balance(account_number)
                    elif choice2 == '4':
                        to_account = int(input("Enter destination account number: "))
                        amount = float(input("Enter amount to transfer: "))
                        bank.transfer(account_number, to_account, amount, password)  # Pass password
                    elif choice2 == '5':
                        bank.delete_account(account_number, password)  # Pass password
                        break
                    elif choice2 == '6':
                        break
                    else:
                        print("Invalid option. Please try again.")
            elif choice == '2':
                first_name = input("Enter your First Name: ")
                last_name = input("Enter your Last Name: ")
                mobile_num = int(input("Enter your 10 digit Mobile Number: "))
                aadhaar_num = int(input("Enter your 12 digit Aadhaar Number: "))
                password = input("Set your password: ")
                bank.create_account(first_name, last_name, mobile_num, aadhaar_num, password)
            elif choice == '3':
                sys.exit()
            else:
                print("Invalid option. Please try again.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
