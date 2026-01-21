import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import time
from datetime import datetime, timedelta
import threading
import traceback
from flask import Flask
import json
import sqlite3
from pathlib import Path

# --------- LOGGING ---------
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger('TimerBot')

# --------- DATABASE SETUP ---------
DB_PATH = Path('timer_bot.db')

def init_database():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # User themes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_themes (
                user_id INTEGER PRIMARY KEY,
                theme_name TEXT DEFAULT 'dark',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Timer history table (optional - for statistics)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS timer_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                duration INTEGER,
                message TEXT,
                completed BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")

init_database()

# --------- DATABASE HELPERS ---------
def get_user_theme(user_id):
    """Get user theme from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT theme_name FROM user_themes WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 'dark'
    except Exception as e:
        logger.error(f"Error getting user theme: {e}")
        return 'dark'

def set_user_theme(user_id, theme_name):
    """Save user theme to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_themes (user_id, theme_name, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET 
                theme_name = excluded.theme_name,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id, theme_name))
        conn.commit()
        conn.close()
        logger.info(f"Theme saved for user {user_id}: {theme_name}")
    except Exception as e:
        logger.error(f"Error saving user theme: {e}")

def save_timer_history(user_id, duration, message, completed):
    """Save timer to history"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO timer_history (user_id, duration, message, completed)
            VALUES (?, ?, ?, ?)
        ''', (user_id, duration, message, completed))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving timer history: {e}")

# --------- KEEP ALIVE ---------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot is alive and running!"

@app.route("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bot_ready": bot.is_ready() if 'bot' in globals() else False,
        "active_timers": len(bot.active_timers) if 'bot' in globals() else 0
    }

def run_web():
    try:
        app.run(host="0.0.0.0", port=3000)
    except Exception as e:
        logger.error(f"Flask error: {e}")

threading.Thread(target=run_web, daemon=True).start()

# --------- ASCII NUMBERS ---------
ASCII_NUMBERS = {
    '0': [
        " ███████╗ ",
        "██╔════██╗",
        "██║█╗█╗██║",
        "██████╔╝██║",
        "╚██████╔╝ ",
        " ╚═════╝  "
    ],
    '1': [
        " ██╗",
        "███║",
        "╚██║",
        " ██║",
        " ██║",
        " ╚═╝"
    ],
    '2': [
        "███████╗ ",
        "╚══════██╗",
        " ███████╔╝",
        "██╔═══╝  ",
        "███████╗ ",
        "╚══════╝ "
    ],
    '3': [
        "███████╗ ",
        "╚══════██╗",
        " ███████╔╝",
        " ╚════██╗ ",
        "███████╔╝ ",
        "╚══════╝  "
    ],
    '4': [
        "██╗  ██╗",
        "██║  ██║",
        "███████║",
        "╚════██║",
        "     ██║",
        "     ╚═╝"
    ],
    '5': [
        "███████╗",
        "██╔════╝",
        "███████╗",
        "╚════██║",
        "███████║",
        "╚══════╝"
    ],
    '6': [
        " ███████╗ ",
        "██╔═══╝  ",
        "███████╗ ",
        "██╔════██╗",
        "╚███████╔╝",
        " ╚══════╝ "
    ],
    '7': [
        "███████╗",
        "╚═════██║",
        "    ██╔╝",
        "   ██╔╝ ",
        "   ██║  ",
        "   ╚═╝  "
    ],
    '8': [
        " █████╗ ",
        "██╔══██╗",
        "╚█████╔╝",
        "██╔══██╗",
        "╚█████╔╝",
        " ╚════╝ "
    ],
    '9': [
        " █████╗ ",
        "██╔══██╗",
        "╚██████║",
        " ╚═══██║",
        " █████╔╝",
        " ╚════╝ "
    ],
    ':': [
        "   ",
        "██╗",
        "╚═╝",
        "██╗",
        "╚═╝",
        "   "
    ]
}

# --------- THEMES ---------
THEMES = {
    'dark': {
        'color': 0x2b2d31,
        'emoji': '🌙',
        'name': 'الثيم الغامق'
    },
    'colorful': {
        'color': 0xFF1493,
        'emoji': '🌈',
        'name': 'الثيم الملون'
    },
    'minimal': {
        'color': 0xFFFFFF,
        'emoji': '⚪',
        'name': 'الثيم البسيط'
    },
    'ocean': {
        'color': 0x1E90FF,
        'emoji': '🌊',
        'name': 'ثيم المحيط'
    },
    'sunset': {
        'color': 0xFF6B35,
        'emoji': '🌅',
        'name': 'ثيم الغروب'
    },
    'forest': {
        'color': 0x228B22,
        'emoji': '🌲',
        'name': 'ثيم الغابة'
    },
    'galaxy': {
        'color': 0x9B59B6,
        'emoji': '🌌',
        'name': 'ثيم المجرة'
    }
}

# --------- HELPER FUNCTIONS ---------
def create_ascii_time(minutes, seconds):
    """Create ASCII art for time display"""
    try:
        time_str = f"{minutes:02d}:{seconds:02d}"
        lines = ['', '', '', '', '', '']
        
        for char in time_str:
            if char in ASCII_NUMBERS:
                for i, line in enumerate(ASCII_NUMBERS[char]):
                    lines[i] += line + ' '
        
        return '\n'.join(lines)
    except Exception as e:
        logger.error(f"Error creating ASCII time: {e}")
        return f"{minutes:02d}:{seconds:02d}"

def create_progress_bar(current, total, length=20):
    """Create a progress bar with emoji"""
    try:
        if total <= 0:
            return "▒" * length + " 0%"
        
        filled = int((current / total) * length)
        filled = max(0, min(filled, length))
        
        # Use different emoji based on progress
        if current / total > 0.75:
            fill_char = '🟩'
        elif current / total > 0.50:
            fill_char = '🟨'
        elif current / total > 0.25:
            fill_char = '🟧'
        else:
            fill_char = '🟥'
        
        empty_char = '⬜'
        
        bar = fill_char * filled + empty_char * (length - filled)
        percentage = int((current / total) * 100)
        return f"{bar} {percentage}%"
    except Exception as e:
        logger.error(f"Error creating progress bar: {e}")
        return "Error"

def parse_time(time_str):
    """Parse time string like '5m', '2h', '30s', '1h30m'"""
    try:
        time_str = str(time_str).lower().strip()
        total_seconds = 0
        
        # Handle combined format like "1h30m"
        import re
        
        # Extract hours
        hours_match = re.search(r'(\d+)h', time_str)
        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600
        
        # Extract minutes
        minutes_match = re.search(r'(\d+)m', time_str)
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60
        
        # Extract seconds
        seconds_match = re.search(r'(\d+)s', time_str)
        if seconds_match:
            total_seconds += int(seconds_match.group(1))
        
        # If no unit found, default to minutes
        if total_seconds == 0 and time_str.isdigit():
            total_seconds = int(time_str) * 60
        
        if total_seconds <= 0:
            raise ValueError("Duration must be greater than 0")
        
        return total_seconds
        
    except (ValueError, AttributeError) as e:
        logger.error(f"Error parsing time '{time_str}': {e}")
        raise ValueError(f"صيغة الوقت غير صحيحة: {time_str}\nاستخدم: 5m, 2h, 30s, أو 1h30m")

def format_time(seconds):
    """Format seconds to readable Arabic time"""
    try:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}س")
        if minutes > 0:
            parts.append(f"{minutes}د")
        if secs > 0 or len(parts) == 0:
            parts.append(f"{secs}ث")
        
        return " ".join(parts)
    except Exception as e:
        logger.error(f"Error formatting time: {e}")
        return "Unknown"

def validate_duration(seconds):
    """Validate timer duration"""
    if seconds <= 0:
        raise ValueError("المدة يجب أن تكون أكبر من 0")
    if seconds > 86400:  # Max 24 hours
        raise ValueError("الحد الأقصى 24 ساعة")
    if seconds < 10:  # Min 10 seconds
        raise ValueError("الحد الأدنى 10 ثواني")
    return True

# --------- DISCORD BOT ---------
intents = discord.Intents.default()
intents.message_content = True

class TimerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.active_timers = {}
        
    async def setup_hook(self):
        try:
            await self.tree.sync()
            logger.info("✅ Slash commands synced successfully!")
        except Exception as e:
            logger.error(f"❌ Error syncing commands: {e}")
            logger.error(traceback.format_exc())

bot = TimerBot()

# --------- TIMER VIEW ---------
class TimerView(discord.ui.View):
    def __init__(self, timer_id, bot_instance):
        super().__init__(timeout=None)
        self.timer_id = timer_id
        self.bot = bot_instance
        
    @discord.ui.button(label="إيقاف مؤقت", style=discord.ButtonStyle.primary, emoji="⏸️")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.timer_id not in self.bot.active_timers:
                await interaction.response.send_message("❌ التايمر غير موجود", ephemeral=True)
                return
                
            timer = self.bot.active_timers[self.timer_id]
            
            # Check if user owns this timer
            if timer['user'].id != interaction.user.id:
                await interaction.response.send_message("❌ هذا التايمر ليس لك", ephemeral=True)
                return
            
            timer['paused'] = not timer.get('paused', False)
            
            if timer['paused']:
                button.label = "استئناف"
                button.emoji = "▶️"
                button.style = discord.ButtonStyle.success
                await interaction.response.edit_message(view=self)
                await interaction.followup.send("⏸️ تم إيقاف التايمر مؤقتاً", ephemeral=True)
            else:
                button.label = "إيقاف مؤقت"
                button.emoji = "⏸️"
                button.style = discord.ButtonStyle.primary
                await interaction.response.edit_message(view=self)
                await interaction.followup.send("▶️ تم استئناف التايمر", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in pause button: {e}")
            logger.error(traceback.format_exc())
            try:
                await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(label="إلغاء", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.timer_id not in self.bot.active_timers:
                await interaction.response.send_message("❌ التايمر غير موجود", ephemeral=True)
                return
                
            timer = self.bot.active_timers[self.timer_id]
            
            # Check if user owns this timer
            if timer['user'].id != interaction.user.id:
                await interaction.response.send_message("❌ هذا التايمر ليس لك", ephemeral=True)
                return
            
            self.bot.active_timers[self.timer_id]['cancelled'] = True
            await interaction.response.send_message("✅ تم إلغاء التايمر", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in cancel button: {e}")
            logger.error(traceback.format_exc())
            try:
                await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(label="+5 دقائق", style=discord.ButtonStyle.success, emoji="➕")
    async def add_time_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.timer_id not in self.bot.active_timers:
                await interaction.response.send_message("❌ التايمر غير موجود", ephemeral=True)
                return
                
            timer = self.bot.active_timers[self.timer_id]
            
            # Check if user owns this timer
            if timer['user'].id != interaction.user.id:
                await interaction.response.send_message("❌ هذا التايمر ليس لك", ephemeral=True)
                return
            
            self.bot.active_timers[self.timer_id]['end_time'] += 300
            self.bot.active_timers[self.timer_id]['total_seconds'] += 300
            await interaction.response.send_message("✅ تم إضافة 5 دقائق", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in add time button: {e}")
            logger.error(traceback.format_exc())
            try:
                await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)
            except:
                pass

# --------- ERROR HANDLER ---------
@bot.event
async def on_command_error(ctx, error):
    logger.error(f"Command error: {error}")
    logger.error(traceback.format_exc())

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    logger.error(f"App command error: {error}")
    logger.error(traceback.format_exc())
    
    error_message = "❌ حدث خطأ غير متوقع"
    
    if isinstance(error, app_commands.CommandOnCooldown):
        error_message = f"⏰ يرجى الانتظار {error.retry_after:.1f} ثانية"
    elif isinstance(error, app_commands.MissingPermissions):
        error_message = "❌ ليس لديك الصلاحيات الكافية"
    
    try:
        if interaction.response.is_done():
            await interaction.followup.send(error_message, ephemeral=True)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)
    except Exception as e:
        logger.error(f"Error sending error message: {e}")

# --------- EVENTS ---------
@bot.event
async def on_ready():
    logger.info(f"""
╔═══════════════════════════════════════╗
║     🤖 Timer Bot Ready!              ║
║     📝 Logged in as: {bot.user.name}
║     🆔 Bot ID: {bot.user.id}
║     🌐 Servers: {len(bot.guilds)}
║     👥 Users: {sum(g.member_count for g in bot.guilds)}
╚═══════════════════════════════════════╝
    """)
    
    # Set bot status
    try:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="⏰ /timer | /help"
            )
        )
    except Exception as e:
        logger.error(f"Error setting presence: {e}")

# --------- TIMER COMMAND ---------
@bot.tree.command(name="timer", description="ابدأ تايمر جديد")
@app_commands.describe(
    duration="المدة (مثال: 5m, 2h, 30s, 1h30m)",
    message="رسالة التذكير (اختياري)"
)
async def timer_command(interaction: discord.Interaction, duration: str, message: str = None):
    try:
        logger.info(f"Timer command: user={interaction.user.name}, duration={duration}, message={message}")
        
        # Parse and validate duration
        total_seconds = parse_time(duration)
        validate_duration(total_seconds)
        
        logger.info(f"Parsed duration: {total_seconds} seconds")
        
        # Get user theme from database
        theme_name = get_user_theme(interaction.user.id)
        theme = THEMES.get(theme_name, THEMES['dark'])
        
        # Create timer ID
        timer_id = f"{interaction.user.id}_{int(time.time())}"
        
        # Create initial embed
        embed = discord.Embed(
            title=f"{theme['emoji']} تايمر جديد",
            description=message or "⏰ تايمر قيد التشغيل...",
            color=theme['color']
        )
        
        # Initial time display
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        ascii_time = create_ascii_time(minutes, seconds)
        
        embed.add_field(
            name="الوقت المتبقي",
            value=f"```\n{ascii_time}\n```",
            inline=False
        )
        
        progress = create_progress_bar(total_seconds, total_seconds)
        embed.add_field(name="التقدم", value=progress, inline=False)
        embed.add_field(name="المدة الكلية", value=format_time(total_seconds), inline=True)
        embed.add_field(name="بدأ في", value=f"<t:{int(time.time())}:T>", inline=True)
        
        # Add footer
        if interaction.user.avatar:
            embed.set_footer(text=f"طلب بواسطة {interaction.user.name}", icon_url=interaction.user.avatar.url)
        else:
            embed.set_footer(text=f"طلب بواسطة {interaction.user.name}")
        
        # Create view
        view = TimerView(timer_id, bot)
        
        # Send message
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        
        # Store timer info
        bot.active_timers[timer_id] = {
            'end_time': time.time() + total_seconds,
            'total_seconds': total_seconds,
            'message': message,
            'user': interaction.user,
            'msg': msg,
            'theme': theme,
            'paused': False,
            'cancelled': False,
            'pause_time': 0,
            'created_at': time.time()
        }
        
        logger.info(f"Timer {timer_id} created successfully")
        
        # Start timer loop
        bot.loop.create_task(run_timer(timer_id))
        
    except ValueError as e:
        error_msg = f"❌ {str(e)}\n\n**أمثلة صحيحة:**\n• `5m` = 5 دقائق\n• `2h` = ساعتين\n• `30s` = 30 ثانية\n• `1h30m` = ساعة ونصف"
        await interaction.response.send_message(error_msg, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in timer command: {e}")
        logger.error(traceback.format_exc())
        
        error_msg = f"❌ حدث خطأ: {str(e)}"
        try:
            if interaction.response.is_done():
                await interaction.followup.send(error_msg, ephemeral=True)
            else:
                await interaction.response.send_message(error_msg, ephemeral=True)
        except:
            pass

async def run_timer(timer_id):
    """Run the timer countdown with improved performance"""
    try:
        logger.info(f"Starting timer: {timer_id}")
        timer = bot.active_timers.get(timer_id)
        
        if not timer:
            logger.error(f"Timer {timer_id} not found")
            return
        
        update_interval = 5  # Update every 5 seconds by default
        last_update = 0
        
        while True:
            try:
                # Check if cancelled
                if timer.get('cancelled'):
                    logger.info(f"Timer {timer_id} cancelled")
                    
                    embed = discord.Embed(
                        title="❌ تم إلغاء التايمر",
                        description=timer['message'] or "التايمر ملغي",
                        color=0xFF0000
                    )
                    
                    try:
                        await timer['msg'].edit(embed=embed, view=None)
                    except:
                        pass
                    
                    # Save to history
                    save_timer_history(timer['user'].id, timer['total_seconds'], timer['message'], False)
                    del bot.active_timers[timer_id]
                    break
                
                # Handle pause
                if timer.get('paused'):
                    if timer['pause_time'] == 0:
                        timer['pause_time'] = time.time()
                    await asyncio.sleep(1)
                    continue
                elif timer['pause_time'] > 0:
                    pause_duration = time.time() - timer['pause_time']
                    timer['end_time'] += pause_duration
                    timer['pause_time'] = 0
                
                # Calculate remaining time
                remaining = int(timer['end_time'] - time.time())
                
                # Check if finished
                if remaining <= 0:
                    logger.info(f"Timer {timer_id} completed")
                    
                    embed = discord.Embed(
                        title="🔔 انتهى الوقت!",
                        description=timer['message'] or "⏰ انتهى التايمر!",
                        color=0x00FF00
                    )
                    embed.add_field(name="المستخدم", value=timer['user'].mention, inline=False)
                    embed.set_footer(text="✅ اكتمل")
                    
                    try:
                        await timer['msg'].edit(embed=embed, view=None)
                        await timer['msg'].reply(f"🔔 {timer['user'].mention} انتهى وقت التايمر! {timer['message'] or ''}")
                    except Exception as e:
                        logger.error(f"Error sending completion: {e}")
                    
                    # Save to history
                    save_timer_history(timer['user'].id, timer['total_seconds'], timer['message'], True)
                    del bot.active_timers[timer_id]
                    break
                
                # Dynamic update interval
                if remaining < 60:
                    update_interval = 2  # Update every 2 seconds in last minute
                else:
                    update_interval = 5
                
                # Only update if enough time passed
                current_time = time.time()
                if current_time - last_update < update_interval:
                    await asyncio.sleep(1)
                    continue
                
                last_update = current_time
                
                # Update display
                minutes = remaining // 60
                seconds = remaining % 60
                ascii_time = create_ascii_time(minutes, seconds)
                
                embed = discord.Embed(
                    title=f"{timer['theme']['emoji']} تايمر قيد التشغيل",
                    description=timer['message'] or "⏰ تايمر قيد التشغيل...",
                    color=timer['theme']['color']
                )
                
                embed.add_field(
                    name="الوقت المتبقي",
                    value=f"```\n{ascii_time}\n```",
                    inline=False
                )
                
                progress = create_progress_bar(remaining, timer['total_seconds'])
                embed.add_field(name="التقدم", value=progress, inline=False)
                embed.add_field(name="المتبقي", value=format_time(remaining), inline=True)
                embed.add_field(name="ينتهي في", value=f"<t:{int(timer['end_time'])}:T>", inline=True)
                
                # Warning messages
                if remaining <= 60 and remaining > 55:
                    embed.add_field(name="⚠️ تنبيه", value="أقل من دقيقة!", inline=False)
                elif remaining <= 300 and remaining > 295:
                    embed.add_field(name="⚠️ تنبيه", value="أقل من 5 دقائق!", inline=False)
                
                if timer['user'].avatar:
                    embed.set_footer(text=f"طلب بواسطة {timer['user'].name}", icon_url=timer['user'].avatar.url)
                else:
                    embed.set_footer(text=f"طلب بواسطة {timer['user'].name}")
                
                # Update message
                try:
                    await timer['msg'].edit(embed=embed)
                except discord.NotFound:
                    logger.warning(f"Timer message deleted: {timer_id}")
                    del bot.active_timers[timer_id]
                    break
                except discord.HTTPException as e:
                    logger.error(f"HTTP error updating timer: {e}")
                    await asyncio.sleep(10)  # Wait longer on rate limit
                except Exception as e:
                    logger.error(f"Error updating timer: {e}")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in timer loop: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
            
    except Exception as e:
        logger.error(f"Fatal error in run_timer {timer_id}: {e}")
        logger.error(traceback.format_exc())
        if timer_id in bot.active_timers:
            del bot.active_timers[timer_id]

# --------- TIMERS LIST COMMAND ---------
@bot.tree.command(name="timers", description="عرض جميع التايمرات النشطة")
async def timers_command(interaction: discord.Interaction):
    try:
        user_timers = {k: v for k, v in bot.active_timers.items() if v['user'].id == interaction.user.id}
        
        if not user_timers:
            await interaction.response.send_message("🔭 ليس لديك أي تايمرات نشطة", ephemeral=True)
            return
        
        theme_name = get_user_theme(interaction.user.id)
        theme = THEMES.get(theme_name, THEMES['dark'])
        
        embed = discord.Embed(
            title=f"{theme['emoji']} تايمراتك النشطة ({len(user_timers)})",
            color=theme['color']
        )
        
        for i, (timer_id, timer) in enumerate(user_timers.items(), 1):
            remaining = int(timer['end_time'] - time.time())
            status = "⏸️ متوقف" if timer.get('paused') else "▶️ يعمل"
            
            created_ago = int(time.time() - timer['created_at'])
            
            embed.add_field(
                name=f"{i}. {timer['message'][:30] if timer['message'] else 'تايمر'}",
                value=f"{status} - متبقي: **{format_time(remaining)}**\nبدأ منذ: {format_time(created_ago)}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in timers command: {e}")
        logger.error(traceback.format_exc())
        await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)

# --------- THEME COMMAND ---------
@bot.tree.command(name="theme", description="اختر ثيم التايمر")
@app_commands.describe(theme_name="اسم الثيم")
@app_commands.choices(theme_name=[
    app_commands.Choice(name="🌙 الثيم الغامق", value="dark"),
    app_commands.Choice(name="🌈 الثيم الملون", value="colorful"),
    app_commands.Choice(name="⚪ الثيم البسيط", value="minimal"),
    app_commands.Choice(name="🌊 ثيم المحيط", value="ocean"),
    app_commands.Choice(name="🌅 ثيم الغروب", value="sunset"),
    app_commands.Choice(name="🌲 ثيم الغابة", value="forest"),
    app_commands.Choice(name="🌌 ثيم المجرة", value="galaxy"),
])
async def theme_command(interaction: discord.Interaction, theme_name: str):
    try:
        # Save to database
        set_user_theme(interaction.user.id, theme_name)
        
        theme = THEMES[theme_name]
        
        embed = discord.Embed(
            title=f"{theme['emoji']} تم تغيير الثيم",
            description=f"تم اختيار **{theme['name']}**\n\nسيتم تطبيقه على التايمرات الجديدة",
            color=theme['color']
        )
        
        # Show preview
        embed.add_field(name="معاينة", value="هذا هو شكل التايمرات الجديدة", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"User {interaction.user.name} changed theme to {theme_name}")
        
    except Exception as e:
        logger.error(f"Error in theme command: {e}")
        logger.error(traceback.format_exc())
        await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)

# --------- STATS COMMAND ---------
@bot.tree.command(name="stats", description="عرض إحصائياتك")
async def stats_command(interaction: discord.Interaction):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user stats
        cursor.execute('''
            SELECT COUNT(*), SUM(duration), SUM(CASE WHEN completed THEN 1 ELSE 0 END)
            FROM timer_history
            WHERE user_id = ?
        ''', (interaction.user.id,))
        
        total, total_time, completed = cursor.fetchone()
        conn.close()
        
        if not total or total == 0:
            await interaction.response.send_message("📊 لم تستخدم التايمر بعد", ephemeral=True)
            return
        
        theme_name = get_user_theme(interaction.user.id)
        theme = THEMES.get(theme_name, THEMES['dark'])
        
        embed = discord.Embed(
            title="📊 إحصائياتك",
            color=theme['color']
        )
        
        embed.add_field(name="🎯 إجمالي التايمرات", value=f"**{total}**", inline=True)
        embed.add_field(name="✅ المكتملة", value=f"**{completed}**", inline=True)
        embed.add_field(name="❌ الملغية", value=f"**{total - completed}**", inline=True)
        
        if total_time:
            embed.add_field(name="⏱️ الوقت الكلي", value=f"**{format_time(total_time)}**", inline=False)
        
        completion_rate = (completed / total * 100) if total > 0 else 0
        embed.add_field(name="📈 نسبة الإكمال", value=f"**{completion_rate:.1f}%**", inline=False)
        
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        logger.error(traceback.format_exc())
        await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)

# --------- PING COMMAND ---------
@bot.tree.command(name="ping", description="فحص سرعة البوت")
async def ping_command(interaction: discord.Interaction):
    try:
        latency = round(bot.latency * 1000)
        
        if latency < 100:
            emoji = "🟢"
            status = "ممتاز"
        elif latency < 200:
            emoji = "🟡"
            status = "جيد"
        else:
            emoji = "🔴"
            status = "بطيء"
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"{emoji} **{latency}ms** - {status}",
            color=0x00FF00
        )
        
        embed.add_field(name="التايمرات النشطة", value=f"**{len(bot.active_timers)}**", inline=True)
        embed.add_field(name="السيرفرات", value=f"**{len(bot.guilds)}**", inline=True)
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in ping command: {e}")
        logger.error(traceback.format_exc())
        await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)

# --------- HELP COMMAND ---------
@bot.tree.command(name="help", description="عرض قائمة المساعدة")
async def help_command(interaction: discord.Interaction):
    try:
        embed = discord.Embed(
            title="📚 قائمة أوامر البوت",
            description="جميع الأوامر المتاحة:",
            color=0x5865F2
        )
        
        embed.add_field(
            name="/timer <المدة> [رسالة]",
            value="ابدأ تايمر جديد\nمثال: `/timer 5m` أو `/timer 1h30m اذاكر`",
            inline=False
        )
        
        embed.add_field(
            name="/timers",
            value="عرض جميع تايمراتك النشطة",
            inline=False
        )
        
        embed.add_field(
            name="/theme <اسم الثيم>",
            value="تغيير ثيم التايمر (7 ثيمات متاحة)",
            inline=False
        )
        
        embed.add_field(
            name="/stats",
            value="عرض إحصائياتك مع التايمر",
            inline=False
        )
        
        embed.add_field(
            name="/ping",
            value="فحص سرعة استجابة البوت",
            inline=False
        )
        
        embed.add_field(
            name="صيغ الوقت المدعومة:",
            value="• `5m` = 5 دقائق\n• `2h` = ساعتين\n• `30s` = 30 ثانية\n• `1h30m` = ساعة ونصف",
            inline=False
        )
        
        embed.add_field(
            name="🎮 الأزرار التفاعلية:",
            value="⏸️ **إيقاف/استئناف** - أوقف التايمر مؤقتاً\n❌ **إلغاء** - ألغي التايمر نهائياً\n➕ **+5 دقائق** - أضف 5 دقائق للتايمر",
            inline=False
        )
        
        embed.set_footer(text="تم التطوير بواسطة Dark | النسخة 2.0")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        logger.error(traceback.format_exc())
        await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)

# --------- RUN BOT ---------
if __name__ == "__main__":
    try:
        token = os.environ.get("TOKEN")
        
        if not token:
            logger.error("❌ No TOKEN found in environment variables!")
            logger.error("Please set TOKEN in your environment")
            exit(1)
        
        logger.info("🚀 Starting Timer Bot v2.0...")
        logger.info("📦 Enhanced with database, better error handling, and more features")
        bot.run(token, log_handler=None)  # Use custom logging
        
    except discord.LoginFailure:
        logger.error("❌ Failed to login - Invalid TOKEN!")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error(traceback.format_exc())