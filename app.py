import matplotlib.pyplot as plt
from mplsoccer.pitch import Pitch
import streamlit as st
import requests
import os
from matplotlib import font_manager as fm
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from io import BytesIO
from matplotlib.colors import to_rgba
import pandas as pd
from matplotlib.table import Table
from PIL import Image
from urllib.request import urlopen
from datetime import datetime
from mplsoccer import Pitch, add_image
import base64
import io

plt.rcParams["figure.dpi"] = 300

st.set_page_config(
    page_title="Süper Lig - Maç Raporu",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
        /* Sidebar içindeki tüm text input elementlerini hedef alma */
        input[id^="text_input"] {
            background-color: #242C3A !important;  /* Arka plan rengi */
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    html, body, [class*="cache"], [class*="st-"]  {
        font-family: 'Poppins', sans-serif;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
        /* Bilgisayarlar için */
        @media (min-width: 1024px) {
            .block-container {
                width: 1000px;
                max-width: 1000px;
                padding-top: 40px;
            }
        }

        /* Tabletler için (genellikle 768px - 1024px arası ekran genişliği) */
        @media (min-width: 768px) and (max-width: 1023px) {
            .block-container.st-emotion-cache-13ln4jf.ea3mdgi5 {
                width: 700px;
                max-width: 700px;
            }
        }

        /* Telefonlar için (genellikle 768px ve altı ekran genişliği) */
        @media (max-width: 767px) {
            .block-container.st-emotion-cache-13ln4jf.ea3mdgi5 {
                width: 100%;
                max-width: 100%;
                padding-left: 10px;
                padding-right: 10px;
            }
        }
        .stDownloadButton {
            display: flex;
            justify-content: center;
            text-align: center;
        }
        .stDownloadButton button {
            background-color: rgba(51, 51, 51, 0.17);
            color: gray;  /* Text color */
            border: 0.5px solid gray;  /* Thin gray border */
            transition: background-color 0.5s ease;
        }
        .stDownloadButton button:hover {
            background-color: rgba(51, 51, 51, 0.65);
            border: 1px solid gray;  /* Thin gray border */
            color: gray;  /* Text color */
        }
        .stDownloadButton button:active {
            background-color: rgba(51, 51, 51, 0.17);
            color: gray;  /* Text color */
            border: 0.5px solid gray;  /* Thin gray border */
            transition: background-color 0.5s ease;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar'a görsel ekleme
image_url = "https://images.fotmob.com/image_resources/logo/leaguelogo/71.png"  # Görselin URL'si

# Görseli bir HTML div ile ortalama
image_html = f"""<div style="display: flex; justify-content: center;">
        <img src="{image_url}" width="100">
    </div>
    """

st.sidebar.markdown(image_html, unsafe_allow_html=True)

# CSS ile fullscreen butonunu gizleme
hide_fullscreen_button = """
    <style>
    button[title="View fullscreen"] {
        display: none;
    }
    </style>
    """
st.sidebar.markdown(hide_fullscreen_button, unsafe_allow_html=True)

plt.rcParams['figure.dpi'] = 300
current_dir = os.path.dirname(os.path.abspath(__file__))

# Poppins fontunu yükleme
font_path = os.path.join(current_dir, 'fonts', 'Poppins-Regular.ttf')
prop = fm.FontProperties(fname=font_path)

bold_font_path = os.path.join(current_dir, 'fonts', 'Poppins-SemiBold.ttf')
bold_prop = fm.FontProperties(fname=bold_font_path)

pitch = Pitch(pitch_type='uefa', pitch_color='#0e1117', line_color='#818f86', goal_type='box')
fig, ax = pitch.draw(figsize=(16, 12.5), tight_layout=True)
fig.set_facecolor('#0e1117')
ax.axis('off')

primary_text_color = '#818f86'

# API'den maç verilerini çekmek için bir fonksiyon
def fetch_finished_matches():
    api_url = "https://www.fotmob.com/api/leagues?id=71&ccode3=TUR"
    response = requests.get(api_url)
    data = response.json()
    allmatches = data['matches']['allMatches']
    
    finished_matches = []
    for match in allmatches:
        if match['status']['finished']:
            finished_matches.append(match)
    
    return finished_matches

# Biten maçları çek
finished_matches = fetch_finished_matches()

# Haftaları ve maçları hazırlamak için bir sözlük oluştur
matches_by_week = {}
for match in finished_matches:
    # Haftayı belirlemek için match['round'] kullanılabilir
    week_number = f"Hafta {match['round']}"
    if week_number not in matches_by_week:
        matches_by_week[week_number] = []
    matches_by_week[week_number].append(match)

# Haftaların sıralı listesi
week_options = sorted(matches_by_week.keys(), key=lambda x: int(x.split()[-1]))

# Son haftayı varsayılan olarak seçme
latest_week = week_options[-1]

# Sol tarafta bir selectbox ile hafta seçimi
selected_week = st.sidebar.selectbox("Haftayı Seçin", week_options, index=week_options.index(latest_week))

# Seçilen haftanın maçlarını gösteren dinamik selectbox
matches = matches_by_week[selected_week]
match_options = [f"{match['home']['name']} vs {match['away']['name']}" for match in matches]

# Haftanın son maçını belirleme
latest_match_display = f"{matches[-1]['home']['name']} vs {matches[-1]['away']['name']}"

# Eğer haftanın son maçı varsa seçili olarak ayarla
selected_match = st.sidebar.selectbox(
    "Maç Seçin",
    match_options,
    index=match_options.index(latest_match_display) if latest_match_display in match_options else 0
)

# Seçilen maçın detaylarını bul
match_details = next(match for match in matches_by_week[selected_week] if f"{match['home']['name']} vs {match['away']['name']}" == selected_match)

# Maç detaylarını çekmek için matchId kullan
match_id = match_details['id']
match_api_url = f"https://www.fotmob.com/api/matchDetails?matchId={match_id}"
match_response = requests.get(match_api_url)
match_data = match_response.json()

general_data = match_data['general']
week = general_data['matchRound']
matchDay = general_data['matchTimeUTCDate']
parsed_date = datetime.fromisoformat(matchDay[:-1])
formatted_date = parsed_date.strftime("%d.%m.%Y")
leagueName = general_data['leagueName']
leagueSeason = general_data['parentLeagueSeason']
leagueString = f"{leagueName} - {leagueSeason}"
weekString = f"{week}. Hafta  |  {formatted_date}"
matchDetailString = f"{leagueString}  |  {weekString}"

# Şut haritası verilerini al
shotmap = match_data['content']['shotmap']['shots']
homeTeamId = general_data['homeTeam']['id']
homeTeamName = general_data['homeTeam']['name']
awayTeamId = general_data['awayTeam']['id']
awayTeamName = general_data['awayTeam']['name']

turnuvaID = general_data["parentLeagueId"]
IMAGE_URL_3 = 'https://images.fotmob.com/image_resources/logo/leaguelogo/dark/' + str(turnuvaID) + '.png'
logo_3 = Image.open(urlopen(IMAGE_URL_3))

skor_bilgisi = match_data["header"]["status"]
skor = str(skor_bilgisi["scoreStr"])

pozisyon_bilgisi = pd.DataFrame(match_data["content"]["stats"]["Periods"]["All"]["stats"][0]["stats"][0])
pozisyon_1 = pozisyon_bilgisi["stats"][0]
pozisyon_2 = pozisyon_bilgisi["stats"][1]

bigchances_bilgisi = pd.DataFrame(match_data["content"]["stats"]["Periods"]["All"]["stats"][0]["stats"][4])
bigchances_1 = bigchances_bilgisi["stats"][0]
bigchances_2 = bigchances_bilgisi["stats"][1]

IMAGE_URL_1 = 'https://images.fotmob.com/image_resources/logo/teamlogo/' + str(homeTeamId) + '.png'
logo_1 = Image.open(urlopen(IMAGE_URL_1))
IMAGE_URL_2 = 'https://images.fotmob.com/image_resources/logo/teamlogo/' + str(awayTeamId) + '.png'
logo_2 = Image.open(urlopen(IMAGE_URL_2))

goller = pd.DataFrame(match_data["header"]["teams"])
firstteam_goals = goller.iloc[0]
firstteam_goals_1 = str(firstteam_goals["score"])
tot_goals_1 = firstteam_goals_1
secondteam_goals = goller.iloc[1]
secondteam_goals_1 = str(secondteam_goals["score"])
tot_goals_2 = secondteam_goals_1

df = pd.DataFrame(match_data["content"]["shotmap"]["shots"])

shots1 = df[df["teamId"] == homeTeamId].reset_index()
shots2 = df[df["teamId"] == awayTeamId].reset_index()

shots2['x'] = 105 - shots2['x']
shots2['y'] = 68 - shots2['y']

sot_bilgisi = pd.DataFrame(match_data["content"]["stats"]["Periods"]["All"]["stats"][1]["stats"][3])
shots1_ot = sot_bilgisi["stats"][0]
shots2_ot = sot_bilgisi["stats"][1]

goal_1 = shots1[shots1["eventType"] == "Goal"].copy()
miss_1 = shots1[(shots1["eventType"] == "Miss") | (shots1["eventType"] == "Post")].copy()
blocked_1 = shots1[shots1["eventType"] == "AttemptSaved"].copy()
goal_2 = shots2[shots2["eventType"] == "Goal"].copy()
miss_2 = shots2[(shots2["eventType"] == "Miss") | (shots2["eventType"] == "Post")].copy()
blocked_2 = shots2[shots2["eventType"] == "AttemptSaved"].copy()

toplam_sut_bilgisi = pd.DataFrame(match_data["content"]["stats"]["Periods"]["All"]["stats"][1]["stats"][1])
tot_shots_1 = toplam_sut_bilgisi["stats"][0]
tot_shots_2 = toplam_sut_bilgisi["stats"][1]

#tot_shots_1 = shots1.shape[0]
#xg_1 = shots1["expectedGoals"].sum().round(2)
#tot_shots_2 = shots2.shape[0]
#xg_2 = shots2["expectedGoals"].sum().round(2)

xg_bilgisi = pd.DataFrame(match_data["content"]["stats"]["Periods"]["All"]["stats"][0]["stats"][1])
xg_1 = xg_bilgisi["stats"][0]
xg_2 = xg_bilgisi["stats"][1]

xgop_bilgisi = pd.DataFrame(match_data["content"]["stats"]["Periods"]["All"]["stats"][2]["stats"][2])
xgop_1 = xgop_bilgisi["stats"][0]
xgop_2 = xgop_bilgisi["stats"][1]

xgot_bilgisi = match_data["content"]["stats"]["Periods"]["All"]["stats"][2]["stats"][5]
xgot_1 = xgot_bilgisi["stats"][0]
xgot_2 = xgot_bilgisi["stats"][1]

sc_goal_1 = pitch.scatter(goal_1["x"], goal_1["y"],
                s=goal_1["expectedGoals"]*1200+100,
                c="#ffe11f", alpha=0.9,
                marker="*",
                ax=ax)

sc_goal_2 = pitch.scatter(goal_2["x"], goal_2["y"],
                s=goal_2["expectedGoals"]*1200+100,
                c="#ffe11f", alpha=0.9,
                marker="*",
                ax=ax)

sc_miss_1 = pitch.scatter(miss_1["x"], miss_1["y"],
                s=miss_1["expectedGoals"]*1200+30,
                c="#ff2e2e", alpha=0.9,
                marker="x",
                ax=ax,
                edgecolor="#101010")

sc_miss_2 = pitch.scatter(miss_2["x"], miss_2["y"],
                s=miss_2["expectedGoals"]*1200+30,
                c="#ff2e2e", alpha=0.9,
                marker="x",
                ax=ax,
                edgecolor="#101010")

sc_blocked_1 = pitch.scatter(blocked_1["x"], blocked_1["y"],
                s=blocked_1["expectedGoals"]*1200+50,
                c="#5178ad", alpha=0.9,
                marker="o",
                ax=ax,
                edgecolor="#101010")

sc_blocked_2 = pitch.scatter(blocked_2["x"], blocked_2["y"],
                s=blocked_2["expectedGoals"]*1200+50,
                c="#5178ad", alpha=0.9,
                marker="o",
                ax=ax,
                edgecolor="#101010")

sc_goal_symbol = pitch.scatter(8.5, -3,
                s=600,
                c="#ffe11f", alpha=0.9,
                marker="*",
                ax=ax)

sc_blocked_symbol = pitch.scatter(20.5, -3,
                s=400,
                c="#5178ad", alpha=0.9,
                marker="o",
                ax=ax,
                edgecolor="#101010")

sc_miss_symbol = pitch.scatter(38.5, -3,
                s=300,
                c="#ff2e2e", alpha=0.9,
                marker="x",
                ax=ax,
                edgecolor="#101010")

xg_symbol_1 = pitch.scatter(75.7, -3,
                s=35,
                c="#5178ad", alpha=0.9,
                marker="o",
                ax=ax,
                edgecolor="#101010")

xg_symbol_2 = pitch.scatter(77.1, -3,
                s=150,
                c="#5178ad", alpha=0.9,
                marker="o",
                ax=ax,
                edgecolor="#101010")

xg_symbol_3 = pitch.scatter(79.3, -3,
                s=400,
                c="#5178ad", alpha=0.9,
                marker="o",
                ax=ax,
                edgecolor="#101010")

sc_goal_text = ax.text(10.5, -3.43, "Gol", size=15, fontproperties=prop, color=primary_text_color)
sc_blocked_text = ax.text(22.5, -3.43, "Kurtarış/Blok", size=15, fontproperties=prop, color=primary_text_color)
sc_miss_text = ax.text(40.5, -3.43, "İsabetsiz", size=15, fontproperties=prop, color=primary_text_color)

xG_text = ax.text(72.6, -3.43, "xG: ", size=15, fontproperties=prop, color=primary_text_color)

back_box = dict(boxstyle='round, pad=0.4', facecolor='wheat', alpha=0.7)
back_box_2 = dict(boxstyle='round, pad=0.4', facecolor='#facd5c', alpha=0.5)

ax.text(52.5, 50.5, "Gol", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
ax.text(52.5, 45.5, "Gol Beklentisi (xG)", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
ax.text(52.5, 40.5, "Akan Oyunda xG", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
ax.text(52.5, 35.5, "İsabetli Şutta xG", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
ax.text(52.5, 30.5, "Toplam Şut", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
ax.text(52.5, 25.5, "İsabetli Şut", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
ax.text(52.5, 20.5, "Kaçırılan Goller", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')
ax.text(52.5, 15.5, "Topa Sahip Olma", size=15, ha="center", fontproperties=prop, bbox=back_box, color='black')

ax.text(41, 50.5, str(tot_goals_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(41, 45.5, str(xg_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(41, 40.5, str(xgop_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(41, 35.5, str(xgot_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(41, 30.5, str(tot_shots_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(41, 25.5, str(shots1_ot), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(41, 20.5, str(bigchances_1), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(41, 15.5, str(pozisyon_1)+"%", size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')

ax.text(64, 50.5, str(tot_goals_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(64, 45.5, str(xg_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(64, 40.5, str(xgop_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(64, 35.5, str(xgot_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(64, 30.5, str(tot_shots_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(64, 25.5, str(shots2_ot), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(64, 20.5, str(bigchances_2), size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
ax.text(64, 15.5, str(pozisyon_2)+"%", size=15, ha="center", fontproperties=prop, bbox=back_box_2, color='black')

ax.text(41, 55, str(homeTeamName), size=18, ha="center", fontproperties=bold_prop, color='white', alpha=0.5)
ax.text(64, 55, str(awayTeamName), size=18, ha="center", fontproperties=bold_prop, color='white', alpha=0.5)

ax_image_1 = add_image(logo_1, fig, left=0.37, bottom=0.76, width=0.06, interpolation='hanning', alpha=0.5)
ax_image_2 = add_image(logo_2, fig, left=0.57, bottom=0.76, width=0.06, interpolation='hanning', alpha=0.5)
ax_image_3 = add_image(logo_3, fig, left=0.05, bottom=0.90, width=0.055, interpolation='hanning')

ax.legend(facecolor='None', edgecolor='None', labelcolor='white', fontsize=20, loc='lower center', ncol=3, 
        alignment='center', columnspacing=1, handletextpad=0.4, prop=prop, bbox_to_anchor=(0.5, -0.02))

plt.gcf().text(0.0137,0.198, '@bariscanyeksin', va='center', fontsize=15,
                    fontproperties=prop, color=primary_text_color, rotation=270)

# Set the title
fig.text(0.115, 0.945, homeTeamName + " " + skor + " " + awayTeamName, size=30, ha="left", fontproperties=bold_prop, color='white')
fig.text(0.115, 0.905, matchDetailString, size=20, ha="left", fontproperties=prop, color=primary_text_color)

ax.text(94.75, -3.43, "Veri: FotMob", size=15, fontproperties=prop, color=primary_text_color)

fig.text(0.075, 0.160, awayTeamName.upper() + " ŞUTLARI", size=14, ha="left", fontproperties=bold_prop, color=primary_text_color)
fig.text(0.925, 0.160, homeTeamName.upper() + " ŞUTLARI", size=14, ha="right", fontproperties=bold_prop, color=primary_text_color)

fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

ax.axis('off')
# Görseli göster
st.pyplot(fig)

homeTeamName_replaced = str(homeTeamName).replace(' ', '_')
awayTeamName_replaced = str(awayTeamName).replace(' ', '_')
match_name_replaced = f"{homeTeamName_replaced}_{awayTeamName_replaced}"
date_replaced = formatted_date.replace('.', '_')
    
buf = io.BytesIO()
plt.savefig(buf, format="png", dpi = 300, bbox_inches = "tight")
buf.seek(0)
file_name = f"{match_name_replaced}_{date_replaced}_Maç_Raporu.png"

st.download_button(
    label="Grafiği İndir",
    data=buf,
    file_name=file_name,
    mime="image/png"
)

# Function to convert image to base64
def img_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Signature section
st.sidebar.markdown("---")  # Add a horizontal line to separate your signature from the content

# Load and encode icons
twitter_icon_base64 = img_to_base64("icons/twitter.png")
github_icon_base64 = img_to_base64("icons/github.png")
twitter_icon_white_base64 = img_to_base64("icons/twitter_white.png")  # White version of Twitter icon
github_icon_white_base64 = img_to_base64("icons/github_white.png")  # White version of GitHub icon

# Display the icons with links at the bottom of the sidebar
st.sidebar.markdown(
    f"""
    <style>
    .sidebar {{
        width: auto;
    }}
    .sidebar-content {{
        display: flex;
        flex-direction: column;
        height: 100%;
        margin-top: 10px;
    }}
    .icon-container {{
        display: flex;
        justify-content: center;
        margin-top: auto;
        padding-bottom: 20px;
        gap: 30px;  /* Space between icons */
    }}
    .icon-container img {{
        transition: filter 0.5s cubic-bezier(0.4, 0, 0.2, 1);  /* Smooth and natural easing */
    }}
    .icon-container a:hover img {{
        filter: brightness(0) invert(1);  /* Inverts color to white */
    }}
    </style>
    <div class="sidebar-content">
        <!-- Other sidebar content like selectbox goes here -->
        <div class="icon-container">
            <a href="https://x.com/bariscanyeksin" target="_blank">
                <img src="data:image/png;base64,{twitter_icon_base64}" alt="Twitter" width="30">
            </a>
            <a href="https://github.com/bariscanyeksin" target="_blank">
                <img src="data:image/png;base64,{github_icon_base64}" alt="GitHub" width="30">
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
