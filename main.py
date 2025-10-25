from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot çalışıyor! ✅"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from discord.utils import get
from datetime import datetime

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "tierlist.json"
LOGS_FILE = "logs_channels.json"
COOLDOWN_FILE = "cooldowns.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_logs_channels():
    if not os.path.exists(LOGS_FILE):
        return {}
    with open(LOGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_logs_channels(data):
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_cooldowns():
    if not os.path.exists(COOLDOWN_FILE):
        return {}
    with open(COOLDOWN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cooldowns(data):
    with open(COOLDOWN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def check_cooldown(user_id: int, kit_name: str) -> bool:
    """Kullanıcının belirli kit için cooldown'ı var mı kontrol eder"""
    cooldowns = load_cooldowns()
    user_id_str = str(user_id)
    
    if user_id_str not in cooldowns:
        return False
    
    if kit_name not in cooldowns[user_id_str]:
        return False
    
    last_use = cooldowns[user_id_str][kit_name]
    current_time = datetime.now().timestamp()
    cooldown_time = 5 * 24 * 60 * 60  # 5 gün saniye cinsinden
    
    return (current_time - last_use) < cooldown_time

def add_cooldown(user_id: int, kit_name: str):
    """Kullanıcıya belirli kit için cooldown ekler"""
    cooldowns = load_cooldowns()
    user_id_str = str(user_id)
    
    if user_id_str not in cooldowns:
        cooldowns[user_id_str] = {}
    
    cooldowns[user_id_str][kit_name] = datetime.now().timestamp()
    save_cooldowns(cooldowns)

def get_remaining_cooldown(user_id: int, kit_name: str) -> int:
    """Kalan cooldown süresini saniye olarak döndürür"""
    cooldowns = load_cooldowns()
    user_id_str = str(user_id)
    
    if user_id_str not in cooldowns or kit_name not in cooldowns[user_id_str]:
        return 0
    
    last_use = cooldowns[user_id_str][kit_name]
    current_time = datetime.now().timestamp()
    cooldown_time = 5 * 24 * 60 * 60  # 5 gün
    
    remaining = cooldown_time - (current_time - last_use)
    return max(0, int(remaining))

def get_tier_roles_for_kit(kit_name: str):
    """Belirli kit için tier rol seçeneklerini döndürür"""
    tiers = ["HT1", "LT1", "HT2", "LT2", "HT3", "LT3", "HT4", "LT4", "HT5", "LT5"]
    roles = []
    
    for tier in tiers:
        role_name = f"{tier} {kit_name}"
        roles.append(app_commands.Choice(name=role_name, value=role_name))
    
    return roles

def get_all_tier_roles():
    """Tüm tier rol seçeneklerini döndürür (genel kullanım için)"""
    roles = []
    kits = ["Nethpot", "Beast", "Diapot", "Gapple", "Elytra"]
    tiers = ["HT1", "LT1", "HT2", "LT2", "HT3", "LT3", "HT4", "LT4", "HT5", "LT5"]
    
    for kit in kits:
        for tier in tiers:
            roles.append(app_commands.Choice(name=f"{tier} {kit}", value=f"{tier} {kit}"))
    
    return roles

async def send_log(guild_id: int, embed: discord.Embed):
    """Log mesajını belirtilen sunucunun log kanalına gönderir"""
    logs_data = load_logs_channels()
    guild_id_str = str(guild_id)
    
    if guild_id_str not in logs_data:
        return
    
    channel_id = logs_data[guild_id_str]
    channel = client.get_channel(channel_id)
    
    if channel:
        try:
            await channel.send(embed=embed)
        except:
            pass  # Kanal bulunamazsa veya mesaj gönderilemezse sessizce geç

@client.event
async def on_ready():
    client.add_view(TicketPanel())
    await client.tree.sync()
    print(f"✅ Bot giriş yaptı: {client.user}")

# ——————— Cooldown Sıfırlama Komutu ———————

@client.tree.command(name="cd-sıfırla", description="Belirtilen üyenin cooldown'ını sıfırlar.")
@app_commands.describe(üye="Cooldown'ı sıfırlanacak üye")
async def cd_sifirla(interaction: discord.Interaction, üye: discord.Member):
    if not any(r.name.lower() == "kurucu" for r in interaction.user.roles):
        return await interaction.response.send_message(
            "❌ Bu komutu sadece **Kurucu** rolüne sahip kullanıcılar kullanabilir.", ephemeral=True
        )
    
    cooldowns = load_cooldowns()
    user_id_str = str(üye.id)
    
    if user_id_str in cooldowns:
        cooldowns[user_id_str] = {}
        save_cooldowns(cooldowns)
        
    embed = discord.Embed(
        title="✅ Cooldown Sıfırlandı",
        description=f"{üye.mention} kullanıcısının tüm cooldown'ları sıfırlandı.",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.set_footer(text=f"İşlemi yapan: {interaction.user}", icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Log gönder
    log_embed = discord.Embed(
        title="🔄 Cooldown Sıfırlandı",
        description="Bir kullanıcının cooldown'ı sıfırlandı.",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    log_embed.add_field(name="İşlemi Yapan", value=interaction.user.mention, inline=True)
    log_embed.add_field(name="Etkilenen Kullanıcı", value=üye.mention, inline=True)
    
    await send_log(interaction.guild_id, log_embed)

# ——————— Tier komutları ———————

@client.tree.command(name="logs", description="Logs kanalını ayarlar.")
@app_commands.describe(kanal="Log mesajlarının gönderileceği kanal")
async def logs(interaction: discord.Interaction, kanal: discord.TextChannel):
    if not any(r.name.lower() == "kurucu" for r in interaction.user.roles):
        return await interaction.response.send_message(
            "❌ Bu komutu sadece **Kurucu** rolüne sahip kullanıcılar kullanabilir.", ephemeral=True
        )
    
    logs_data = load_logs_channels()
    guild_id = str(interaction.guild_id)
    logs_data[guild_id] = kanal.id
    save_logs_channels(logs_data)
    
    embed = discord.Embed(
        title="📋 Logs Kanalı Ayarlandı",
        description=f"Log kanalı {kanal.mention} olarak ayarlandı.",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.set_footer(text=f"Ayarlayan: {interaction.user}", icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # İlk log mesajını gönder
    log_embed = discord.Embed(
        title="🔧 Sistem Ayarları",
        description="Logs kanalı başarıyla ayarlandı!",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    log_embed.add_field(name="Ayarlayan", value=interaction.user.mention, inline=True)
    log_embed.add_field(name="Kanal", value=kanal.mention, inline=True)
    
    await send_log(interaction.guild_id, log_embed)

# ——————— Kur Komutu ———————

@client.tree.command(name="kur", description="Tüm tier rollerini kurar.")
async def kur(interaction: discord.Interaction):
    if not any(r.name.lower() == "kurucu" for r in interaction.user.roles):
        return await interaction.response.send_message(
            "❌ Bu komutu sadece **Kurucu** rolüne sahip kullanıcılar kullanabilir.", ephemeral=True
        )
    
    roles_to_create = [
        # Nethpot Tiers
        "HT1 Nethpot", "LT1 Nethpot", "HT2 Nethpot", "LT2 Nethpot", "HT3 Nethpot", 
        "LT3 Nethpot", "HT4 Nethpot", "LT4 Nethpot", "HT5 Nethpot", "LT5 Nethpot",
        # Beast Tiers  
        "HT1 Beast", "LT1 Beast", "HT2 Beast", "LT2 Beast", "HT3 Beast", 
        "LT3 Beast", "HT4 Beast", "LT4 Beast", "HT5 Beast", "LT5 Beast",
        # Diapot Tiers
        "HT1 Diapot", "LT1 Diapot", "HT2 Diapot", "LT2 Diapot", "HT3 Diapot", 
        "LT3 Diapot", "HT4 Diapot", "LT4 Diapot", "HT5 Diapot", "LT5 Diapot",
        # Gapple Tiers
        "HT1 Gapple", "LT1 Gapple", "HT2 Gapple", "LT2 Gapple", "HT3 Gapple", 
        "LT3 Gapple", "HT4 Gapple", "LT4 Gapple", "HT5 Gapple", "LT5 Gapple",
        # Elytra Tiers
        "HT1 Elytra", "LT1 Elytra", "HT2 Elytra", "LT2 Elytra", "HT3 Elytra", 
        "LT3 Elytra", "HT4 Elytra", "LT4 Elytra", "HT5 Elytra", "LT5 Elytra",
        # Tester Roles
        "Nethpot Tester",
        "Diapot Tester",  
        "Beast Tester",
        "Elytra Tester",
        "Gapple Tester",
    ]
    
    created_roles = []
    existing_roles = []
    
    await interaction.response.defer(ephemeral=True)
    
    for role_name in roles_to_create:
        existing_role = discord.utils.get(interaction.guild.roles, name=role_name)
        if existing_role:
            existing_roles.append(role_name)
            continue
        
        try:
            await interaction.guild.create_role(
                name=role_name,
                permissions=discord.Permissions.none(),
                hoist=False,
                mentionable=True
            )
            created_roles.append(role_name)
        except discord.HTTPException:
            continue
    
    embed = discord.Embed(
        title="🎭 Rol Kurulum Raporu",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    if created_roles:
        embed.add_field(
            name=f"✅ Oluşturulan Roller ({len(created_roles)})",
            value=f"```{', '.join(created_roles[:20])}{'...' if len(created_roles) > 20 else ''}```",
            inline=False
        )
    
    if existing_roles:
        embed.add_field(
            name=f"⚠️ Zaten Mevcut ({len(existing_roles)})",
            value=f"```{', '.join(existing_roles[:20])}{'...' if len(existing_roles) > 20 else ''}```",
            inline=False
        )
    
    embed.set_footer(text=f"İşlemi yapan: {interaction.user}", icon_url=interaction.user.display_avatar.url)
    
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    # Log gönder
    log_embed = discord.Embed(
        title="🎭 Roller Kuruldu",
        description="Tier rolleri kurulum işlemi yapıldı.",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    log_embed.add_field(name="Kuran", value=interaction.user.mention, inline=True)
    log_embed.add_field(name="Oluşturulan", value=str(len(created_roles)), inline=True)
    log_embed.add_field(name="Zaten Mevcut", value=str(len(existing_roles)), inline=True)
    
    await send_log(interaction.guild_id, log_embed)

# ——————— Tier Remove Komutu ———————

@client.tree.command(name="tier_remove", description="Kullanıcıyı tier'dan çıkar ve rolünü al.")
@app_commands.describe(kullanıcı="Silinecek kullanıcı", rol="Silinecek rol")
async def tier_remove(interaction: discord.Interaction, kullanıcı: discord.Member, rol: discord.Role):
    if not any(r.name.lower() == "tester" for r in interaction.user.roles):
        return await interaction.response.send_message(
            "❌ Bu komutu sadece **Tester** rolüne sahip kullanıcılar kullanabilir.", ephemeral=True
        )

    data = load_data(); gid = str(interaction.guild_id); rid = str(rol.id)
    if gid not in data or rid not in data[gid] or str(kullanıcı.id) not in data[gid][rid]:
        return await interaction.response.send_message(
            f"{kullanıcı.mention} `{rol.name}` tier'ında bulunamadı.", ephemeral=True
        )

    data[gid][rid].remove(str(kullanıcı.id)); save_data(data)
    
    mesaj_ek = ""
    if rol in kullanıcı.roles:
        await kullanıcı.remove_roles(rol)
        mesaj_ek = f"`{rol.name}` rolü kaldırıldı."
    else:
        mesaj_ek = f"`{rol.name}` kullanıcıda zaten yoktu."
    
    await interaction.response.send_message(f"{kullanıcı.mention} `{rol.name}` tier'ından çıkarıldı. {mesaj_ek}")
    
    # Log gönder
    log_embed = discord.Embed(
        title="🗑️ Tier Silme",
        description="Bir kullanıcı tier listesinden çıkarıldı.",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    log_embed.add_field(name="İşlemi Yapan", value=interaction.user.mention, inline=True)
    log_embed.add_field(name="Etkilenen Kullanıcı", value=kullanıcı.mention, inline=True)
    log_embed.add_field(name="Tier (Rol)", value=rol.mention, inline=True)
    log_embed.add_field(name="Durum", value=mesaj_ek, inline=False)
    
    await send_log(interaction.guild_id, log_embed)

@client.tree.command(name="tier_show", description="Tüm tier listesini gösterir.")
async def tier_show(interaction: discord.Interaction):
    data = load_data(); gid = str(interaction.guild_id)
    if gid not in data or not data[gid]:
        return await interaction.response.send_message("Sunucuda kayıtlı tier verisi yok.", ephemeral=True)

    embed = discord.Embed(title="📊 Tier Listesi", color=discord.Color.blurple())
    for rid, uids in data[gid].items():
        role = interaction.guild.get_role(int(rid))
        if not role: continue
        mentions = [
            interaction.guild.get_member(int(u)).mention
            for u in uids
            if interaction.guild.get_member(int(u))
        ]
        embed.add_field(name=role.name, value=", ".join(mentions) if mentions else "-", inline=False)

    await interaction.response.send_message(embed=embed)
    
    # Log gönder
    log_embed = discord.Embed(
        title="📋 Tier Listesi Görüntülendi",
        description="Tier listesi görüntülendi.",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    log_embed.add_field(name="Görüntüleyen", value=interaction.user.mention, inline=True)
    log_embed.add_field(name="Kanal", value=interaction.channel.mention, inline=True)
    
    await send_log(interaction.guild_id, log_embed)

# ——————— TierVer Komutları - Kit Bazlı ———————

# Nethpot için TierVer komutu
@client.tree.command(name="tierver-nethpot", description="Nethpot kit için tier verir.")
@app_commands.describe(
    user="Oyuncu (etiketle)",
    tester="Tester (etiketle)",
    oyun_içi_isim="Oyun içi isim",
    yeni_tier="Yeni Nethpot Tier seç",
    eski_tier="Eski Nethpot Tier seç",
    skor="Maç skoru (örn. 2-1)",
    sunucu="Sunucu adı",
    kazanan="Kazanan (etiketle)"
)
@app_commands.choices(
    yeni_tier=get_tier_roles_for_kit("Nethpot"),
    eski_tier=get_tier_roles_for_kit("Nethpot")
)
async def tierver_nethpot(
    interaction: discord.Interaction,
    user: discord.Member,
    tester: discord.Member,
    oyun_içi_isim: str,
    yeni_tier: str,
    eski_tier: str,
    skor: str,
    sunucu: str,
    kazanan: discord.Member
):
    await handle_tierver(interaction, "Nethpot", user, tester, oyun_içi_isim, yeni_tier, eski_tier, skor, sunucu, kazanan)

# Diapot için TierVer komutu
@client.tree.command(name="tierver-diapot", description="Diapot kit için tier verir.")
@app_commands.describe(
    user="Oyuncu (etiketle)",
    tester="Tester (etiketle)",
    oyun_içi_isim="Oyun içi isim",
    yeni_tier="Yeni Diapot Tier seç",
    eski_tier="Eski Diapot Tier seç",
    skor="Maç skoru (örn. 2-1)",
    sunucu="Sunucu adı",
    kazanan="Kazanan (etiketle)"
)
@app_commands.choices(
    yeni_tier=get_tier_roles_for_kit("Diapot"),
    eski_tier=get_tier_roles_for_kit("Diapot")
)
async def tierver_diapot(
    interaction: discord.Interaction,
    user: discord.Member,
    tester: discord.Member,
    oyun_içi_isim: str,
    yeni_tier: str,
    eski_tier: str,
    skor: str,
    sunucu: str,
    kazanan: discord.Member
):
    await handle_tierver(interaction, "Diapot", user, tester, oyun_içi_isim, yeni_tier, eski_tier, skor, sunucu, kazanan)

# Beast için TierVer komutu
@client.tree.command(name="tierver-beast", description="Beast kit için tier verir.")
@app_commands.describe(
    user="Oyuncu (etiketle)",
    tester="Tester (etiketle)",
    oyun_içi_isim="Oyun içi isim",
    yeni_tier="Yeni Beast Tier seç",
    eski_tier="Eski Beast Tier seç",
    skor="Maç skoru (örn. 2-1)",
    sunucu="Sunucu adı",
    kazanan="Kazanan (etiketle)"
)
@app_commands.choices(
    yeni_tier=get_tier_roles_for_kit("Beast"),
    eski_tier=get_tier_roles_for_kit("Beast")
)
async def tierver_beast(
    interaction: discord.Interaction,
    user: discord.Member,
    tester: discord.Member,
    oyun_içi_isim: str,
    yeni_tier: str,
    eski_tier: str,
    skor: str,
    sunucu: str,
    kazanan: discord.Member
):
    await handle_tierver(interaction, "Beast", user, tester, oyun_içi_isim, yeni_tier, eski_tier, skor, sunucu, kazanan)

# Gapple için TierVer komutu
@client.tree.command(name="tierver-gapple", description="Gapple kit için tier verir.")
@app_commands.describe(
    user="Oyuncu (etiketle)",
    tester="Tester (etiketle)",
    oyun_içi_isim="Oyun içi isim",
    yeni_tier="Yeni Gapple Tier seç",
    eski_tier="Eski Gapple Tier seç",
    skor="Maç skoru (örn. 2-1)",
    sunucu="Sunucu adı",
    kazanan="Kazanan (etiketle)"
)
@app_commands.choices(
    yeni_tier=get_tier_roles_for_kit("Gapple"),
    eski_tier=get_tier_roles_for_kit("Gapple")
)
async def tierver_gapple(
    interaction: discord.Interaction,
    user: discord.Member,
    tester: discord.Member,
    oyun_içi_isim: str,
    yeni_tier: str,
    eski_tier: str,
    skor: str,
    sunucu: str,
    kazanan: discord.Member
):
    await handle_tierver(interaction, "Gapple", user, tester, oyun_içi_isim, yeni_tier, eski_tier, skor, sunucu, kazanan)

# Elytra için TierVer komutu
@client.tree.command(name="tierver-elytra", description="Elytra kit için tier verir.")
@app_commands.describe(
    user="Oyuncu (etiketle)",
    tester="Tester (etiketle)",
    oyun_içi_isim="Oyun içi isim",
    yeni_tier="Yeni Elytra Tier seç",
    eski_tier="Eski Elytra Tier seç",
    skor="Maç skoru (örn. 2-1)",
    sunucu="Sunucu adı",
    kazanan="Kazanan (etiketle)"
)
@app_commands.choices(
    yeni_tier=get_tier_roles_for_kit("Elytra"),
    eski_tier=get_tier_roles_for_kit("Elytra")
)
async def tierver_elytra(
    interaction: discord.Interaction,
    user: discord.Member,
    tester: discord.Member,
    oyun_içi_isim: str,
    yeni_tier: str,
    eski_tier: str,
    skor: str,
    sunucu: str,
    kazanan: discord.Member
):
    await handle_tierver(interaction, "Elytra", user, tester, oyun_içi_isim, yeni_tier, eski_tier, skor, sunucu, kazanan)

# Ortak TierVer İşleyici Fonksiyon
async def handle_tierver(
    interaction: discord.Interaction,
    kit: str,
    user: discord.Member,
    tester: discord.Member,
    oyun_içi_isim: str,
    yeni_tier: str,
    eski_tier: str,
    skor: str,
    sunucu: str,
    kazanan: discord.Member
):
    # Kit-specific tester role kontrolü - sadece kit-özel rol yeterli
    required_role = f"{kit} Tester"
    if not any(r.name == required_role for r in interaction.user.roles):
        return await interaction.response.send_message(f"❌ Bu komutu kullanabilmek için `{required_role}` rolüne sahip olmanız gerekir.", ephemeral=True)

    # Rol objelerini bul
    yeni_tier_role = discord.utils.get(interaction.guild.roles, name=yeni_tier)
    eski_tier_role = discord.utils.get(interaction.guild.roles, name=eski_tier)
    
    if not yeni_tier_role:
        return await interaction.response.send_message(f"❌ `{yeni_tier}` rolü bulunamadı!", ephemeral=True)

    # Veritabanına ekle
    data = load_data(); gid = str(interaction.guild_id); tid = str(yeni_tier_role.id)
    data.setdefault(gid, {}).setdefault(tid, [])
    if str(user.id) not in data[gid][tid]:
        data[gid][tid].append(str(user.id)); save_data(data)

    # Rolleri güncelle
    if eski_tier_role and eski_tier_role in user.roles:
        await user.remove_roles(eski_tier_role)
    if yeni_tier_role not in user.roles:
        await user.add_roles(yeni_tier_role)

    # Rapor gönder
    channel = discord.utils.get(interaction.guild.channels, name=f"🏆┃{kit.lower()}-sonuçlar")
    if not channel:
        return await interaction.response.send_message(f"❌ `🏆┃{kit.lower()}-sonuçlar` kanalı bulunamadı!", ephemeral=True)

    embed = discord.Embed(title=f"🏆 {oyun_içi_isim} {kit} Test Sonuçları:", color=discord.Color.orange())
    embed.add_field(name="Discord:", value=user.mention, inline=True)
    embed.add_field(name="Tester:", value=tester.mention, inline=True)
    embed.add_field(name="Oyun içi isim:", value=oyun_içi_isim, inline=False)
    embed.add_field(name="Yeni Tier:", value=yeni_tier_role.mention, inline=True)
    embed.add_field(name="Eski Tier:", value=eski_tier_role.mention if eski_tier_role else eski_tier, inline=True)
    embed.add_field(name="Sonuçlar:", value=skor, inline=False)
    embed.add_field(name="Sunucu:", value=sunucu, inline=False)

    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Kaydedildi, rol verildi ve rapor gönderildi.", ephemeral=True)
    
    # Log
    log_embed = discord.Embed(title="🏆 Tier Verme", color=discord.Color.green(), timestamp=datetime.now())
    log_embed.add_field(name="Yapan", value=interaction.user.mention, inline=True)
    log_embed.add_field(name="Oyuncu", value=user.mention, inline=True)
    log_embed.add_field(name="Kit", value=kit, inline=True)
    log_embed.add_field(name="Yeni Tier", value=yeni_tier, inline=True)
    log_embed.add_field(name="Skor", value=skor, inline=True)
    await send_log(interaction.guild_id, log_embed)

# ——————— Ticket Form Modal ———————

class TicketFormModal(discord.ui.Modal, title="Ticket Formu"):
    def __init__(self, kit_name: str):
        super().__init__()
        self.kit_name = kit_name
    
    kullanici_adi = discord.ui.TextInput(
        label="Kullanıcı Adı",
        placeholder="Minecraft kullanıcı adınızı girin...",
        required=True,
        max_length=50
    )
    
    sunucu = discord.ui.TextInput(
        label="Sunucu",
        placeholder="Hangi sunucuda oynuyorsunuz?",
        required=True,
        max_length=100
    )
    
    eski_tier = discord.ui.TextInput(
        label="Eski Tier",
        placeholder="Mevcut tier'ınız (isteğe bağlı)",
        required=False,
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        # Kategoriyi bul
        category = next((c for c in interaction.guild.categories if c.name.lower() == self.kit_name.lower()), None)
        if not category:
            return await interaction.response.send_message(f"❌ `{self.kit_name}` kategorisi bulunamadı!", ephemeral=True)

        # Kanal adını oluştur
        name = f"ticket-{interaction.user.name.lower()}-{self.kit_name.lower()}"
        if get(interaction.guild.channels, name=name):
            return await interaction.response.send_message("❌ Zaten açık bir ticketın var!", ephemeral=True)

        # Sadece bu kit için tester rolünü bul
        kit_tester_role = get(interaction.guild.roles, name=f"{self.kit_name} Tester")
        
        if not kit_tester_role:
            return await interaction.response.send_message(f"❌ `{self.kit_name} Tester` rolü bulunamadı!", ephemeral=True)

        # Kanal izinlerini ayarla - SADECE kit-özel tester rolü görebilir
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True),
            kit_tester_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        # Genel "Tester" rolünü açıkça engelle
        general_tester_role = get(interaction.guild.roles, name="Tester")
        if general_tester_role:
            overwrites[general_tester_role] = discord.PermissionOverwrite(view_channel=False)

        # Ticket kanalını oluştur
        try:
            ticket_chan = await interaction.guild.create_text_channel(
                name=name,
                category=category,
                overwrites=overwrites,
                reason=f"{self.kit_name} ticket açıldı"
            )
        except Exception as e:
            return await interaction.response.send_message(f"❌ Ticket kanalı oluşturulamadı: {str(e)}", ephemeral=True)

        # Form bilgilerini embed olarak gönder
        form_embed = discord.Embed(
            title=f"🎫 {self.kit_name} Ticket Formu",
            color=discord.Color.dark_gold(),
            timestamp=datetime.now()
        )
        form_embed.add_field(name="👤 Kullanıcı Adı", value=self.kullanici_adi.value, inline=True)
        form_embed.add_field(name="🖥️ Sunucu", value=self.sunucu.value, inline=True)
        form_embed.add_field(name="📊 Eski Tier", value=self.eski_tier.value if self.eski_tier.value else "Belirtilmedi", inline=True)
        form_embed.add_field(name="📝 Açan Kişi", value=interaction.user.mention, inline=False)
        form_embed.set_footer(text="Test için bekleyin, bir tester sizinle iletişime geçecektir.")

        # Sadece kit-özel tester rolünü etiketle
        content = f"{kit_tester_role.mention} Yeni {self.kit_name} ticket açıldı!"
        
        try:
            await ticket_chan.send(content=content, embed=form_embed)
        except Exception as e:
            await ticket_chan.delete()
            return await interaction.response.send_message(f"❌ Ticket mesajı gönderilemedi: {str(e)}", ephemeral=True)

        # Cooldown ekle
        add_cooldown(interaction.user.id, self.kit_name)
        
        await interaction.response.send_message(f"✅ Ticket oluşturuldu: {ticket_chan.mention}", ephemeral=True)
        
        # Log gönder
        log_embed = discord.Embed(
            title="🎫 Ticket Oluşturuldu",
            description="Yeni bir ticket açıldı.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        log_embed.add_field(name="Ticket Açan", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Kit", value=self.kit_name, inline=True)
        log_embed.add_field(name="Kanal", value=ticket_chan.mention, inline=True)
        log_embed.add_field(name="Kullanıcı Adı", value=self.kullanici_adi.value, inline=True)
        log_embed.add_field(name="Sunucu", value=self.sunucu.value, inline=True)
        log_embed.add_field(name="Eski Tier", value=self.eski_tier.value if self.eski_tier.value else "Belirtilmedi", inline=True)
        
        await send_log(interaction.guild_id, log_embed)

# ——————— Ticket Panel ve Close ———————

class TicketSelectMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Nethpot",
                description="Ticket açmak için Nethpot kitini seçin",
                emoji="🧪",
                value="Nethpot"
            ),
            discord.SelectOption(
                label="Diapot",
                description="Ticket açmak için Diapot kitini seçin",
                emoji="💎",
                value="Diapot"
            ),
            discord.SelectOption(
                label="Elytra",
                description="Ticket açmak için Elytra kitini seçin",
                emoji="🪶",
                value="Elytra"
            ),
            discord.SelectOption(
                label="Gapple",
                description="Ticket açmak için Gapple kitini seçin",
                emoji="🍎",
                value="Gapple"
            ),
            discord.SelectOption(
                label="Beast",
                description="Ticket açmak için Beast kitini seçin",
                emoji="🦁",
                value="Beast"
            )
        ]
        
        super().__init__(placeholder="Ticket açmak için kit seçin", options=options, min_values=1, max_values=1, custom_id="ticket_select_menu")
    
    async def callback(self, interaction: discord.Interaction):
        kit_name = self.values[0]
        
        # Cooldown kontrolü
        if check_cooldown(interaction.user.id, kit_name):
            remaining = get_remaining_cooldown(interaction.user.id, kit_name)
            days = remaining // (24 * 60 * 60)
            hours = (remaining % (24 * 60 * 60)) // (60 * 60)
            minutes = (remaining % (60 * 60)) // 60
            
            embed = discord.Embed(
                title="⏰ Cooldown Aktif",
                description=f"Bu kit için tekrar ticket açabilmek için **{days} gün {hours} saat {minutes} dakika** beklemeniz gerekiyor.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        modal = TicketFormModal(kit_name)
        await interaction.response.send_modal(modal)

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelectMenu())

@client.tree.command(name="panel", description="Ticket panelini bu kanala kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="TRTİERLİST",
        description="**Test Olabileceğiniz Kitler:**\nNethpot, Diapot, Beast, Elytra, Gapple, \n\n"
                   "- Eğer bir tierin yoksa veya tierin LT3ün altındaysa istediğin kiti seçerek o kitde ticket oluşturabilirsin.\n\n"
                    "- Test süresi 5 gündür.",
        color=discord.Color.dark_gold()
    )
    await interaction.response.send_message(embed=embed, view=TicketPanel())
    
    log_embed = discord.Embed(title="🎛️ Panel Kuruldu", color=discord.Color.blue(), timestamp=datetime.now())
    log_embed.add_field(name="Kuran", value=interaction.user.mention, inline=True)
    await send_log(interaction.guild_id, log_embed)

@panel.error
async def panel_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Yönetici izni gerekiyor.", ephemeral=True)

@client.tree.command(name="ticket_close", description="Aktif ticket kanalını kapatır.")
@app_commands.describe(ticket="Kapatılacak ticket kanalı")
async def ticket_close(interaction: discord.Interaction, ticket: discord.TextChannel):
    # Kit-özel tester rollerini kontrol et (genel Tester rolü artık hiçbir işlem yapamaz)
    kit_tester_roles = ["Nethpot Tester", "Diapot Tester", "Beast Tester", "Elytra Tester", "Gapple Tester"]
    has_kit_tester_role = any(r.name in kit_tester_roles for r in interaction.user.roles)
    
    # Yönetici kontrolü de ekleyelim
    is_admin = interaction.user.guild_permissions.administrator
    
    if not has_kit_tester_role and not is_admin:
        return await interaction.response.send_message("❌ Bu komutu kullanabilmek için kit-özel tester rollerinden birine sahip olmanız gerekir (Nethpot Tester, Diapot Tester, Beast Tester, Elytra Tester, Gapple Tester).", ephemeral=True)
    if not ticket.name.startswith("ticket-"):
        return await interaction.response.send_message("❌ Bu bir ticket kanalı değil.", ephemeral=True)
    
    log_embed = discord.Embed(title="🗑️ Ticket Kapatıldı", color=discord.Color.red(), timestamp=datetime.now())
    log_embed.add_field(name="Kapatan", value=interaction.user.mention, inline=True)
    log_embed.add_field(name="Kanal", value=ticket.name, inline=True)
    await send_log(interaction.guild_id, log_embed)
    
    await ticket.delete(reason=f"Ticket kapatıldı: {interaction.user}")
    await interaction.response.send_message(f"✅ {ticket.name} kapatıldı.", ephemeral=True)

# ——— BOTU BAŞLAT ———
if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if not token:
        print("❌ TOKEN bulunamadı! Lütfen .env dosyasını veya Replit Secrets'i kontrol edin.")
    else:
        client.run(token)
