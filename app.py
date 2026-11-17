import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yaml

st.set_page_config(page_title="Kuntadonitsi", layout="wide")

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

muni_name = config["municipality"]["name"]
st.title(f"{muni_name}n kaupungin Kuntadonitsi")
st.markdown("Automaattisesti avoimista rajapinnoista (StatFin, THL Sotkanet, SYKE) päivittyvä tilannekuva.")

df = pd.read_csv("doughnut_results.csv")

# Yhteenvetokortit
col1, col2 = st.columns(2)
soc_df = df[df["domain"] == "Sosiaalinen perusta"]
eco_df = df[df["domain"] == "Ekologinen katto"]

col1.metric("Sosiaalinen perusta tavoitteessa", f"{soc_df['is_safe'].sum()} / {len(soc_df)} mittaria")
col2.metric("Ekologinen katto rajoissa", f"{eco_df['is_safe'].sum()} / {len(eco_df)} mittaria")

# Piirretään ympyränmuotoinen kuntadonitsi (Plotly Barpolar)
fig = go.Figure()

colors = ["#2e7d32" if safe else "#c62828" for safe in df["is_safe"]]

fig.add_trace(go.Barpolar(
    r=df["ratio_pct"],
    theta=df["name"],
    marker_color=colors,
    marker_line_color="white",
    marker_line_width=2,
    opacity=0.85,
    customdata=df[["value", "unit", "threshold", "source", "year"]],
    hovertemplate=(
        "%{theta}
"
        "Arvo: %{customdata[0]} %{customdata[1]} (Raja: %{customdata[2]})
"
        "Suhde kestävään rajaan: %{r} %
"
        "Lähde: %{customdata[3]} (%{customdata[4]})"
    )
))

fig.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 350], ticksuffix="%"),
        hole=0.35
    ),
    showlegend=False,
    height=650
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Lähdedata ja kynnysarvot")
st.dataframe(df[["domain", "name", "value", "unit", "threshold", "ratio_pct", "source", "year"]], use_container_width=True)
