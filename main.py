import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import time
from datetime import datetime, timedelta
import threading
from flask import Flask

# --------- KEEP ALIVE ---------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot is alive and running!"

def run_web():
    app.run(host="0.0.0.0", port=3000)

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
    time_str = f"{minutes:02d}:{seconds:02d}"
    lines = ['', '', '', '', '', '']
    
    for char in time_str:
        if char in ASCII_NUMBERS:
            for i, line in enumerate(ASCII_NUMBERS[char]):
                lines[i] += line + ' '
    
    return '\n'.join(lines)

def create_progress_bar(current, total, length=20):
    """Create a progress bar"""
    filled = int((current / total) * length)
    bar = '█' * filled + '░' * (length - filled)
    percentage = int((current / total) * 100)
    return f"{bar} {percentage}%"

def parse_time(time_str):
    """Parse time string like '5m', '2h', '30s'"""
    time_str = time_str.lower().strip()
    
    if time_str.endswith('h'):
        return int(time_str[:-1]) * 3600
    elif time_str.endswith('m'):
        return int(time_str[:-1]) * 60
    elif time_str.endswith('s'):
        return int(time_str[:-1])
    else:
        return int(time_str) * 60  # Default to minutes

def format_time(seconds):
    """Format seconds to readable time"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}س {minutes}د {secs}ث"
    elif minutes > 0:
        return f"{minutes}د {secs}ث"
    else:
        return f"{secs}ث"

# --------- DISCORD BOT ---------
intents = discord.Intents.default()
intents.message_content = True

class TimerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.active_timers = {}
        self.user_themes = {}
        
    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Slash commands synced!")

bot = TimerBot()

# --------- TIMER VIEW ---------
class TimerView(discord.ui.View):
    def __init__(self, timer_id, bot_instance):
        super().__init__(timeout=None)
        self.timer_id = timer_id
        self.bot = bot_instance
        
    @discord.ui.button(label="إيقاف مؤقت", style=discord.ButtonStyle.primary, emoji="⏸️")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
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
    
    @discord.ui.button(label="إلغاء", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.timer_id in self.bot.active_timers:
            self.bot.active_timers[self.timer_id]['cancelled'] = True
            await interaction.response.send_message("✅ تم إلغاء التايمر", ephemeral=True)
        else:
            await interaction.response.send_message("❌ التايمر غير موجود", ephemeral=True)
    
    @discord.ui.button(label="+5 دقائق", style=discord.ButtonStyle.success, emoji="➕")
    async def add_time_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.timer_id in self.bot.active_timers:
            self.bot.active_timers[self.timer_id]['end_time'] += 300
            await interaction.response.send_message("✅ تم إضافة 5 دقائق", ephemeral=True)
        else:
            await interaction.response.send_message("❌ التايمر غير موجود", ephemeral=True)

# --------- EVENTS ---------
@bot.event
async def on_ready():
    print(f"""
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
        total_seconds = parse_time(duration)
        
        if total_seconds <= 0 or total_seconds > 86400:  # Max 24 hours
            await interaction.response.send_message("❌ المدة يجب أن تكون بين 1 ثانية و 24 ساعة", ephemeral=True)
            return
        
        # Get user theme
        theme = THEMES[bot.user_themes.get(interaction.user.id, 'dark')]
        
        # Create timer ID
        timer_id = f"{interaction.user.id}_{int(time.time())}"
        
        # Create embed
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
        embed.set_footer(text=f"طلب بواسطة {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        view = TimerView(timer_id, bot)
        
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
            'pause_time': 0
        }
        
        # Start timer loop
        await run_timer(timer_id)
        
    except ValueError:
        await interaction.response.send_message("❌ صيغة الوقت خاطئة! استخدم: 5m, 2h, أو 30s", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ حدث خطأ: {str(e)}", ephemeral=True)

async def run_timer(timer_id):
    """Run the timer countdown"""
    timer = bot.active_timers.get(timer_id)
    if not timer:
        return
    
    while True:
        if timer.get('cancelled'):
            embed = discord.Embed(
                title="❌ تم إلغاء التايمر",
                description=timer['message'] or "التايمر ملغي",
                color=0xFF0000
            )
            await timer['msg'].edit(embed=embed, view=None)
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
        
        remaining = int(timer['end_time'] - time.time())
        
        if remaining <= 0:
            # Timer finished
            embed = discord.Embed(
                title="🔔 انتهى الوقت!",
                description=timer['message'] or "⏰ انتهى التايمر!",
                color=0x00FF00
            )
            embed.add_field(name="المستخدم", value=timer['user'].mention, inline=False)
            embed.set_footer(text="✅ اكتمل")
            
            await timer['msg'].edit(embed=embed, view=None)
            await timer['msg'].reply(f"🔔 {timer['user'].mention} انتهى وقت التايمر!")
            
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
        
        embed.set_footer(text=f"طلب بواسطة {timer['user'].name}", icon_url=timer['user'].avatar.url if timer['user'].avatar else None)
        
        try:
            await timer['msg'].edit(embed=embed)
        except:
            del bot.active_timers[timer_id]
            break
        
        await asyncio.sleep(5)  # Update every 5 seconds

# --------- TIMERS LIST COMMAND ---------
@bot.tree.command(name="timers", description="عرض جميع التايمرات النشطة")
async def timers_command(interaction: discord.Interaction):
    user_timers = {k: v for k, v in bot.active_timers.items() if v['user'].id == interaction.user.id}
    
    if not user_timers:
        await interaction.response.send_message("📭 ليس لديك أي تايمرات نشطة", ephemeral=True)
        return
    
    theme = THEMES[bot.user_themes.get(interaction.user.id, 'dark')]
    embed = discord.Embed(
        title=f"{theme['emoji']} تايمراتك النشطة",
        color=theme['color']
    )
    
    for timer_id, timer in user_timers.items():
        remaining = int(timer['end_time'] - time.time())
        status = "⏸️ متوقف" if timer.get('paused') else "▶️ يعمل"
        embed.add_field(
            name=f"{timer['message'] or 'تايمر'}",
            value=f"{status} - متبقي: {format_time(remaining)}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

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
    bot.user_themes[interaction.user.id] = theme_name
    theme = THEMES[theme_name]
    
    embed = discord.Embed(
        title=f"{theme['emoji']} تم تغيير الثيم",
        description=f"تم اختيار **{theme['name']}**",
        color=theme['color']
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --------- PING COMMAND ---------
@bot.tree.command(name="ping", description="فحص سرعة البوت")
async def ping_command(interaction: discord.Interaction):
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

# --------- RUN BOT ---------
if __name__ == "__main__":
    try:
        bot.run(os.environ.get("TOKEN"))
    except Exception as e:
        print(f"❌ Error starting bot: {e}")