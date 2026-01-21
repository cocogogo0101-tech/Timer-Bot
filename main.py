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

# --------- LOGGING ---------
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TimerBot')

# --------- KEEP ALIVE ---------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot is alive and running!"

def run_web():
    try:
        app.run(host="0.0.0.0", port=3000)
    except Exception as e:
        logger.error(f"Flask error: {e}")

threading.Thread(target=run_web, daemon=True).start()

# --------- ASCII NUMBERS ---------
ASCII_NUMBERS = {
    '0': [
        " ██████╗ ",
        "██╔═████╗",
        "██║██╔██║",
        "████╔╝██║",
        "╚██████╔╝",
        " ╚═════╝ "
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
        "██████╗ ",
        "╚════██╗",
        " █████╔╝",
        "██╔═══╝ ",
        "███████╗",
        "╚══════╝"
    ],
    '3': [
        "██████╗ ",
        "╚════██╗",
        " █████╔╝",
        " ╚═══██╗",
        "██████╔╝",
        "╚═════╝ "
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
        " ██████╗ ",
        "██╔════╝ ",
        "███████╗ ",
        "██╔═══██╗",
        "╚██████╔╝",
        " ╚═════╝ "
    ],
    '7': [
        "███████╗",
        "╚════██║",
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
    """Create a progress bar"""
    try:
        if total <= 0:
            return "░" * length + " 0%"
        filled = int((current / total) * length)
        filled = max(0, min(filled, length))
        bar = '█' * filled + '░' * (length - filled)
        percentage = int((current / total) * 100)
        return f"{bar} {percentage}%"
    except Exception as e:
        logger.error(f"Error creating progress bar: {e}")
        return "Error"

def parse_time(time_str):
    """Parse time string like '5m', '2h', '30s'"""
    try:
        time_str = str(time_str).lower().strip()
        
        if time_str.endswith('h'):
            return int(time_str[:-1]) * 3600
        elif time_str.endswith('m'):
            return int(time_str[:-1]) * 60
        elif time_str.endswith('s'):
            return int(time_str[:-1])
        else:
            # Default to minutes if no unit
            return int(time_str) * 60
    except ValueError as e:
        logger.error(f"Error parsing time '{time_str}': {e}")
        raise ValueError(f"صيغة الوقت غير صحيحة: {time_str}")

def format_time(seconds):
    """Format seconds to readable time"""
    try:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}س {minutes}د {secs}ث"
        elif minutes > 0:
            return f"{minutes}د {secs}ث"
        else:
            return f"{secs}ث"
    except Exception as e:
        logger.error(f"Error formatting time: {e}")
        return "Unknown"

# --------- DISCORD BOT ---------
intents = discord.Intents.default()
intents.message_content = True

class TimerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.active_timers = {}
        self.user_themes = {}
        
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
            if self.timer_id in self.bot.active_timers:
                timer = self.bot.active_timers[self.timer_id]
                timer['paused'] = not timer.get('paused', False)
                
                if timer['paused']:
                    button.label = "استئناف"
                    button.emoji = "▶️"
                    await interaction.response.edit_message(view=self)
                    await interaction.followup.send("⏸️ تم إيقاف التايمر مؤقتاً", ephemeral=True)
                else:
                    button.label = "إيقاف مؤقت"
                    button.emoji = "⏸️"
                    await interaction.response.edit_message(view=self)
                    await interaction.followup.send("▶️ تم استئناف التايمر", ephemeral=True)
            else:
                await interaction.response.send_message("❌ التايمر غير موجود", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in pause button: {e}")
            await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="إلغاء", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.timer_id in self.bot.active_timers:
                self.bot.active_timers[self.timer_id]['cancelled'] = True
                await interaction.response.send_message("✅ تم إلغاء التايمر", ephemeral=True)
            else:
                await interaction.response.send_message("❌ التايمر غير موجود", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in cancel button: {e}")
            await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="+5 دقائق", style=discord.ButtonStyle.success, emoji="➕")
    async def add_time_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.timer_id in self.bot.active_timers:
                self.bot.active_timers[self.timer_id]['end_time'] += 300
                await interaction.response.send_message("✅ تم إضافة 5 دقائق", ephemeral=True)
            else:
                await interaction.response.send_message("❌ التايمر غير موجود", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in add time button: {e}")
            await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)

# --------- ERROR HANDLER ---------
@bot.event
async def on_command_error(ctx, error):
    logger.error(f"Command error: {error}")
    logger.error(traceback.format_exc())

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    logger.error(f"App command error: {error}")
    logger.error(traceback.format_exc())
    
    try:
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ حدث خطأ: {str(error)}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ حدث خطأ: {str(error)}", ephemeral=True)
    except:
        pass

# --------- EVENTS ---------
@bot.event
async def on_ready():
    logger.info(f"""
╔══════════════════════════════════════╗
║     🤖 Timer Bot Ready!              ║
║     📝 Logged in as: {bot.user.name}
║     🆔 Bot ID: {bot.user.id}
║     🌐 Servers: {len(bot.guilds)}
╚══════════════════════════════════════╝
    """)

# --------- TIMER COMMAND ---------
@bot.tree.command(name="timer", description="ابدأ تايمر جديد")
@app_commands.describe(
    duration="المدة (مثال: 5m, 2h, 30s)",
    message="رسالة التذكير (اختياري)"
)
async def timer_command(interaction: discord.Interaction, duration: str, message: str = None):
    try:
        logger.info(f"Timer command called by {interaction.user.name} with duration: {duration}")
        
        # Parse duration
        total_seconds = parse_time(duration)
        logger.info(f"Parsed duration: {total_seconds} seconds")
        
        # Validate duration
        if total_seconds <= 0:
            await interaction.response.send_message("❌ المدة يجب أن تكون أكبر من 0", ephemeral=True)
            return
            
        if total_seconds > 86400:  # Max 24 hours
            await interaction.response.send_message("❌ الحد الأقصى 24 ساعة (86400 ثانية)", ephemeral=True)
            return
        
        # Get user theme
        theme_name = bot.user_themes.get(interaction.user.id, 'dark')
        theme = THEMES.get(theme_name, THEMES['dark'])
        logger.info(f"Using theme: {theme_name}")
        
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
        embed.add_field(name="التقدم", value=f"`{progress}`", inline=False)
        embed.add_field(name="المدة الكلية", value=format_time(total_seconds), inline=True)
        embed.add_field(name="بدأ في", value=f"<t:{int(time.time())}:T>", inline=True)
        
        # Add footer with user info
        if interaction.user.avatar:
            embed.set_footer(text=f"طلب بواسطة {interaction.user.name}", icon_url=interaction.user.avatar.url)
        else:
            embed.set_footer(text=f"طلب بواسطة {interaction.user.name}")
        
        # Create view
        view = TimerView(timer_id, bot)
        
        # Send message
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        logger.info(f"Timer message sent successfully")
        
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
            'pause_time': 0
        }
        
        logger.info(f"Timer {timer_id} created and stored")
        
        # Start timer loop in background
        bot.loop.create_task(run_timer(timer_id))
        
    except ValueError as e:
        logger.error(f"ValueError in timer command: {e}")
        await interaction.response.send_message(f"❌ صيغة الوقت خاطئة! استخدم: 5m, 2h, أو 30s\nالخطأ: {str(e)}", ephemeral=True)
    except Exception as e:
        logger.error(f"Error in timer command: {e}")
        logger.error(traceback.format_exc())
        
        error_msg = f"❌ حدث خطأ: {str(e)}\n\nيرجى التأكد من:\n- صيغة الوقت صحيحة (5m, 2h, 30s)\n- التوكن صحيح\n- البوت لديه الصلاحيات الكافية"
        
        if interaction.response.is_done():
            await interaction.followup.send(error_msg, ephemeral=True)
        else:
            await interaction.response.send_message(error_msg, ephemeral=True)

async def run_timer(timer_id):
    """Run the timer countdown"""
    try:
        logger.info(f"Starting timer loop for {timer_id}")
        timer = bot.active_timers.get(timer_id)
        
        if not timer:
            logger.error(f"Timer {timer_id} not found in active timers")
            return
        
        while True:
            # Check if cancelled
            if timer.get('cancelled'):
                logger.info(f"Timer {timer_id} was cancelled")
                embed = discord.Embed(
                    title="❌ تم إلغاء التايمر",
                    description=timer['message'] or "التايمر ملغي",
                    color=0xFF0000
                )
                try:
                    await timer['msg'].edit(embed=embed, view=None)
                except:
                    pass
                del bot.active_timers[timer_id]
                break
            
            # Handle pause
            if timer.get('paused'):
                if timer['pause_time'] == 0:
                    timer['pause_time'] = time.time()
                await asyncio.sleep(1)
                continue
            elif timer['pause_time'] > 0:
                # Resume: add paused duration to end_time
                pause_duration = time.time() - timer['pause_time']
                timer['end_time'] += pause_duration
                timer['pause_time'] = 0
            
            # Calculate remaining time
            remaining = int(timer['end_time'] - time.time())
            
            # Check if finished
            if remaining <= 0:
                logger.info(f"Timer {timer_id} finished")
                # Timer finished
                embed = discord.Embed(
                    title="🔔 انتهى الوقت!",
                    description=timer['message'] or "⏰ انتهى التايمر!",
                    color=0x00FF00
                )
                embed.add_field(name="المستخدم", value=timer['user'].mention, inline=False)
                embed.set_footer(text="✅ اكتمل")
                
                try:
                    await timer['msg'].edit(embed=embed, view=None)
                    await timer['msg'].reply(f"🔔 {timer['user'].mention} انتهى وقت التايمر!")
                except Exception as e:
                    logger.error(f"Error sending completion message: {e}")
                
                del bot.active_timers[timer_id]
                break
            
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
            embed.add_field(name="التقدم", value=f"`{progress}`", inline=False)
            embed.add_field(name="المتبقي", value=format_time(remaining), inline=True)
            embed.add_field(name="ينتهي في", value=f"<t:{int(timer['end_time'])}:T>", inline=True)
            
            # Warning if less than 1 minute
            if remaining <= 60 and remaining > 55:
                embed.add_field(name="⚠️ تنبيه", value="أقل من دقيقة!", inline=False)
            
            # Add footer
            if timer['user'].avatar:
                embed.set_footer(text=f"طلب بواسطة {timer['user'].name}", icon_url=timer['user'].avatar.url)
            else:
                embed.set_footer(text=f"طلب بواسطة {timer['user'].name}")
            
            # Update message
            try:
                await timer['msg'].edit(embed=embed)
            except discord.NotFound:
                logger.warning(f"Timer message was deleted for {timer_id}")
                del bot.active_timers[timer_id]
                break
            except Exception as e:
                logger.error(f"Error updating timer message: {e}")
                # Continue anyway
            
            # Wait before next update
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except Exception as e:
        logger.error(f"Error in run_timer for {timer_id}: {e}")
        logger.error(traceback.format_exc())
        if timer_id in bot.active_timers:
            del bot.active_timers[timer_id]

# --------- TIMERS LIST COMMAND ---------
@bot.tree.command(name="timers", description="عرض جميع التايمرات النشطة")
async def timers_command(interaction: discord.Interaction):
    try:
        user_timers = {k: v for k, v in bot.active_timers.items() if v['user'].id == interaction.user.id}
        
        if not user_timers:
            await interaction.response.send_message("📭 ليس لديك أي تايمرات نشطة", ephemeral=True)
            return
        
        theme_name = bot.user_themes.get(interaction.user.id, 'dark')
        theme = THEMES.get(theme_name, THEMES['dark'])
        
        embed = discord.Embed(
            title=f"{theme['emoji']} تايمراتك النشطة ({len(user_timers)})",
            color=theme['color']
        )
        
        for i, (timer_id, timer) in enumerate(user_timers.items(), 1):
            remaining = int(timer['end_time'] - time.time())
            status = "⏸️ متوقف" if timer.get('paused') else "▶️ يعمل"
            embed.add_field(
                name=f"{i}. {timer['message'] or 'تايمر'}",
                value=f"{status} - متبقي: {format_time(remaining)}",
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
])
async def theme_command(interaction: discord.Interaction, theme_name: str):
    try:
        bot.user_themes[interaction.user.id] = theme_name
        theme = THEMES[theme_name]
        
        embed = discord.Embed(
            title=f"{theme['emoji']} تم تغيير الثيم",
            description=f"تم اختيار **{theme['name']}**",
            color=theme['color']
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"User {interaction.user.name} changed theme to {theme_name}")
        
    except Exception as e:
        logger.error(f"Error in theme command: {e}")
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
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"Ping: {latency}ms")
        
    except Exception as e:
        logger.error(f"Error in ping command: {e}")
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
            value="ابدأ تايمر جديد\nمثال: `/timer 5m` أو `/timer 2h اذاكر`",
            inline=False
        )
        
        embed.add_field(
            name="/timers",
            value="عرض جميع تايمراتك النشطة",
            inline=False
        )
        
        embed.add_field(
            name="/theme <اسم الثيم>",
            value="تغيير ثيم التايمر (dark, colorful, minimal, ocean, sunset)",
            inline=False
        )
        
        embed.add_field(
            name="/ping",
            value="فحص سرعة استجابة البوت",
            inline=False
        )
        
        embed.add_field(
            name="صيغ الوقت المدعومة:",
            value="`5m` = 5 دقائق\n`2h` = ساعتين\n`30s` = 30 ثانية",
            inline=False
        )
        
        embed.set_footer(text="استخدم الأزرار للتحكم بالتايمر: ⏸️ إيقاف | ❌ إلغاء | ➕ إضافة وقت")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)

# --------- RUN BOT ---------
if __name__ == "__main__":
    try:
        token = os.environ.get("TOKEN")
        
        if not token:
            logger.error("❌ No TOKEN found in environment variables!")
            logger.error("Please set TOKEN in your environment or hosting platform")
            exit(1)
        
        logger.info("🚀 Starting bot...")
        bot.run(token)
        
    except discord.LoginFailure:
        logger.error("❌ Failed to login - Invalid TOKEN!")
        logger.error("Please check your TOKEN in environment variables")
    except Exception as e:
        logger.error(f"❌ Fatal error starting bot: {e}")
        logger.error(traceback.format_exc())