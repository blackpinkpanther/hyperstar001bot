import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import pandas as pd
from datetime import datetime

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define global variables
user_data = {}

# Define headers for the Excel file
excel_headers = ['Date', 'Name', 'National code', "Snapp driver's name", 'Items', 'Invoice no', 'Time out', 'Time in', 'Staff or LPO']

# Function to handle /start command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome to the Excel Generator Bot! Type /generate to start generating Excel file.')

# Function to handle text messages
def handle_text(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in user_data:
        user_data[user_id] = {'rows': []}

    current_row = {}

    # Add Date
    current_row['Date'] = datetime.now().strftime('%d/%m')

    # Add Name
    current_row['Name'] = context.user_data.get('SV_name', '')

    # Add National code
    while True:
        try:
            national_code = context.user_data.get('national_code', '')
            if national_code and national_code.isdigit() and len(national_code) == 10:
                current_row['National code'] = int(national_code)
                break
            else:
                context.user_data['national_code'] = update.message.reply_text('Enter 10-digit National Code:')
                return
        except ValueError:
            update.message.reply_text('Invalid input. Please enter a 10-digit National Code.')

    # Check for duplicate entries
    if any(entry['National code'] == current_row['National code'] and entry['Date'] == current_row['Date'] for entry in user_data[user_id]['rows']):
        update.message.reply_text('This driver has purchased today. Please enter a new National Code.')
        return

    # Add Snapp driver's name
    current_row["Snapp driver's name"] = update.message.reply_text('Enter Snapp driver\'s name:').text

    # Add Items
    current_row['Items'] = update.message.reply_text('Enter Items:').text

    # Add Invoice no
    while True:
        try:
            invoice_no = update.message.reply_text('Enter Invoice no:')
            if invoice_no.text.isdigit():
                current_row['Invoice no'] = int(invoice_no.text)
                break
            else:
                update.message.reply_text('Please write numbers.')
        except ValueError:
            update.message.reply_text('Invalid input. Please enter a valid number for Invoice no.')

    # Highlight rows if National code has been inputted in dates before the current day
    for entry in user_data[user_id]['rows']:
        if entry['National code'] == current_row['National code'] and entry['Date'] != current_row['Date']:
            current_row['highlight'] = True
            break
    else:
        current_row['highlight'] = False

    # Add Time out
    current_row['Time out'] = datetime.now().strftime('%H:%M')

    # Add Time in (current time of the time when bot asks for the value input for F column)
    current_row['Time in'] = datetime.now().strftime('%H:%M')

    # Add Staff or LPO
    staff_lpo_options = ['LPO', 'Staff', 'none']
    current_row['Staff or LPO'] = update.message.reply_text(f'Select one of the options: {", ".join(staff_lpo_options)}',
                                                             reply_markup={'keyboard': [staff_lpo_options], 'one_time_keyboard': True}).text

    # Append the current row to the user's data
    user_data[user_id]['rows'].append(current_row)

# Function to handle /cancelDiscount command
def cancel_discount(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Check if there is any data to cancel
    if user_id in user_data and user_data[user_id]['rows']:
        # Remove the last row
        user_data[user_id]['rows'].pop()

        update.message.reply_text('Canceled the current row. You can start again.')
    else:
        update.message.reply_text('No row to cancel.')

# Function to handle /generate command
def generate_excel(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Check if there is any data to generate Excel file
    if user_id not in user_data or not user_data[user_id]['rows']:
        update.message.reply_text('No data to generate Excel file.')
        return

    try:
        # Create a DataFrame from the collected data
        df = pd.DataFrame(user_data[user_id]['rows'])

        # Create Excel file with highlighted rows
        file_path = f"{user_id}_excel_file.xlsx"
        df.style.apply(lambda row: ['background: yellow' if row['highlight'] else '' for _ in df.columns], axis=1).to_excel(file_path, index=False)

        # Clear user data
        del user_data[user_id]

        # Send the Excel file to the user
        update.message.reply_document(document=open(file_path, 'rb'), filename='excel_file.xlsx')

    except Exception as e:
        logger.error(f"Error creating Excel file: {str(e)}")
        update.message.reply_text('An error occurred while generating the Excel file. Please try again.')

# Function to handle unknown commands
def unknown(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Sorry, I don't understand that command.")

def main() -> None:
    # Token for the Telegram bot
    updater = Updater(7056934227:AAEegz29avZ9TAf6SAqa1uXsrjSQ46_3uHA)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("generate", generate_excel))
    dp.add_handler(CommandHandler("cancelDiscount", cancel_discount))

    # Register message handler for text messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    # Register unknown command handler
    dp.add_handler(MessageHandler(Filters.command, unknown))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop it
    updater.idle()

if __name__ == '__main__':
    main()
