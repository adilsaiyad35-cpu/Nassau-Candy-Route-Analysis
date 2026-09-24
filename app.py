import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Nassau Candy Shipping Analysis",
    page_icon="🚚",
    layout="wide"
)


# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor.csv")

    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")

    df["Lead Time"] = (df["Ship Date"] - df["Order Date"]).dt.days

    factory_map = {
        "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
        "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
        "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
        "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
        "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
        "Laffy Taffy": "Sugar Shack",
        "SweeTARTS": "Sugar Shack",
        "Nerds": "Sugar Shack",
        "Fun Dip": "Sugar Shack",
        "Fizzy Lifting Drinks": "Sugar Shack",
        "Everlasting Gobstopper": "Secret Factory",
        "Lickable Wallpaper": "Secret Factory",
        "Wonka Gum": "Secret Factory",
        "Hair Toffee": "The Other Factory",
        "Kazookles": "The Other Factory"
    }

    df["Factory"] = df["Product Name"].map(factory_map).fillna("Unknown")

    # Convert state names to two-letter codes for the map
    state_codes = {
        "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ",
        "Arkansas": "AR", "California": "CA", "Colorado": "CO",
        "Connecticut": "CT", "Delaware": "DE", "Florida": "FL",
        "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
        "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
        "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
        "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA",
        "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
        "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
        "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
        "New Mexico": "NM", "New York": "NY",
        "North Carolina": "NC", "North Dakota": "ND",
        "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
        "Pennsylvania": "PA", "Rhode Island": "RI",
        "South Carolina": "SC", "South Dakota": "SD",
        "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
        "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
        "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
        "District of Columbia": "DC"
    }

    state_lookup = {
        name.lower(): code for name, code in state_codes.items()
    }
    state_lookup.update({
        code.lower(): code for code in state_codes.values()
    })

    df["State_Code"] = (
        df["State/Province"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(state_lookup)
    )

    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load the CSV file: {e}")
    st.info("Keep app.py and Nassau Candy Distributor.csv in the same folder.")
    st.stop()


# --------------------------------------------------
# 2. PAGE TITLE
# --------------------------------------------------

st.title("🚚 Factory-to-Customer Shipping Route Efficiency Analysis")
st.caption("Nassau Candy Distributor | Shipping, Sales & Factory Performance")


# --------------------------------------------------
# 3. SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

regions = sorted(df["Region"].dropna().unique())
selected_regions = st.sidebar.multiselect(
    "Select Region", regions, default=regions
)

ship_modes = sorted(df["Ship Mode"].dropna().unique())
selected_modes = st.sidebar.multiselect(
    "Select Ship Mode", ship_modes, default=ship_modes
)

factories = sorted(df["Factory"].dropna().unique())
selected_factories = st.sidebar.multiselect(
    "Select Factory", factories, default=factories
)

states = sorted(df["State/Province"].dropna().unique())
selected_states = st.sidebar.multiselect(
    "Select State / Province", states, default=states
)

min_date = df["Order Date"].min()
max_date = df["Order Date"].max()

if pd.notna(min_date) and pd.notna(max_date):
    date_range = st.sidebar.date_input(
        "Order Date Range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date()
    )
else:
    date_range = None

threshold = st.sidebar.slider(
    "Lead Time Threshold (Days)",
    min_value=0,
    max_value=2000,
    value=10,
    step=1
)


# --------------------------------------------------
# 4. APPLY FILTERS
# --------------------------------------------------

filtered = df[
    df["Region"].isin(selected_regions)
    & df["Ship Mode"].isin(selected_modes)
    & df["Factory"].isin(selected_factories)
    & df["State/Province"].isin(selected_states)
].copy()

if date_range and len(date_range) == 2:
    start_date, end_date = date_range

    filtered = filtered[
        filtered["Order Date"].dt.date.between(start_date, end_date)
    ]

valid_lead = filtered[
    filtered["Lead Time"].notna()
    & (filtered["Lead Time"] >= 0)
].copy()


# --------------------------------------------------
# 5. KPI METRICS
# --------------------------------------------------

total_sales = filtered["Sales"].sum()
total_profit = filtered["Gross Profit"].sum()
total_orders = filtered["Order ID"].nunique()
avg_lead = valid_lead["Lead Time"].mean()

delayed_orders = valid_lead.loc[
    valid_lead["Lead Time"] > threshold, "Order ID"
].nunique()

valid_orders = valid_lead["Order ID"].nunique()

delay_frequency = (
    delayed_orders / valid_orders * 100 if valid_orders else 0
)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Total Sales", f"${total_sales:,.0f}")
c2.metric("Gross Profit", f"${total_profit:,.0f}")
c3.metric("Total Orders", f"{total_orders:,}")
c4.metric(
    "Average Lead Time",
    f"{avg_lead:,.1f} days" if pd.notna(avg_lead) else "N/A"
)
c5.metric("Delay Frequency", f"{delay_frequency:.2f}%")

st.divider()


# --------------------------------------------------
# 6. AVERAGE LEAD TIME BY SHIP MODE
# --------------------------------------------------

st.subheader("Average Lead Time by Ship Mode")

ship_summary = (
    valid_lead.groupby("Ship Mode", as_index=False)["Lead Time"]
    .mean()
    .sort_values("Lead Time")
)

if not ship_summary.empty:
    fig = px.bar(
        ship_summary,
        x="Ship Mode",
        y="Lead Time",
        color="Ship Mode",
        title="Average Lead Time by Ship Mode",
        labels={"Lead Time": "Average Lead Time (Days)"}
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No valid lead-time records for these filters.")


# --------------------------------------------------
# 7. TOTAL SALES BY FACTORY
# --------------------------------------------------

st.subheader("Total Sales by Factory")

factory_sales = (
    filtered.groupby("Factory", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
)

if not factory_sales.empty:
    fig2 = px.bar(
        factory_sales,
        x="Factory",
        y="Sales",
        title="Total Sales by Factory",
        labels={"Sales": "Total Sales"}
    )
    st.plotly_chart(fig2, use_container_width=True)


# --------------------------------------------------
# 8. AVERAGE LEAD TIME BY REGION
# --------------------------------------------------

st.subheader("Average Lead Time by Region")

region_summary = (
    valid_lead.groupby("Region", as_index=False)["Lead Time"]
    .mean()
    .sort_values("Lead Time", ascending=False)
)

if not region_summary.empty:
    fig3 = px.bar(
        region_summary,
        x="Region",
        y="Lead Time",
        title="Average Lead Time by Region",
        labels={"Lead Time": "Average Lead Time (Days)"}
    )
    st.plotly_chart(fig3, use_container_width=True)


# --------------------------------------------------
# 9. DELAY FREQUENCY BY FACTORY
# --------------------------------------------------

st.subheader("Delay Frequency by Factory")

delay_data = valid_lead.copy()
delay_data["Delayed"] = delay_data["Lead Time"] > threshold

order_delay = (
    delay_data.groupby(["Factory", "Order ID"], as_index=False)
    .agg(Delayed=("Delayed", "max"))
)

delay_summary = (
    order_delay.groupby("Factory", as_index=False)
    .agg(
        Total_Orders=("Order ID", "nunique"),
        Delayed_Orders=("Delayed", "sum")
    )
)

delay_summary["Delay_Frequency"] = (
    delay_summary["Delayed_Orders"]
    .div(delay_summary["Total_Orders"].replace(0, pd.NA))
    .mul(100)
)

st.dataframe(
    delay_summary,
    use_container_width=True,
    hide_index=True
)

if not delay_summary.empty:
    fig_delay = px.bar(
        delay_summary,
        x="Factory",
        y="Delay_Frequency",
        title="Delay Frequency by Factory",
        labels={"Delay_Frequency": "Delay Frequency (%)"},
        text=delay_summary["Delay_Frequency"].map(
            lambda value: f"{value:.1f}%" if pd.notna(value) else "N/A"
        )
    )
    fig_delay.update_yaxes(range=[0, 100])
    st.plotly_chart(fig_delay, use_container_width=True)


# --------------------------------------------------
# 10. ROUTE PERFORMANCE & EFFICIENCY SCORE
# --------------------------------------------------

st.divider()
st.header("Route Efficiency Leaderboard")

route_summary = (
    valid_lead.groupby(
        ["Factory", "State/Province"], as_index=False
    )
    .agg(
        Orders=("Order ID", "nunique"),
        Average_Lead_Time=("Lead Time", "mean"),
        Lead_Time_Variability=("Lead Time", "std")
    )
)

if not route_summary.empty:
    min_lead = route_summary["Average_Lead_Time"].min()
    max_lead = route_summary["Average_Lead_Time"].max()

    if max_lead == min_lead:
        route_summary["Efficiency_Score"] = 100.0
    else:
        route_summary["Efficiency_Score"] = (
            (max_lead - route_summary["Average_Lead_Time"])
            / (max_lead - min_lead)
            * 100
        )

    route_summary["Efficiency_Score"] = (
        route_summary["Efficiency_Score"].round(1)
    )

    st.caption(
        "Efficiency Score is relative to the currently filtered routes. "
        "A higher score means a lower average order-to-ship interval; "
        "it is not an external service rating."
    )

    st.subheader("Top 10 Fastest Factory-to-State Routes")

    fastest_routes = route_summary.sort_values(
        ["Average_Lead_Time", "Orders"],
        ascending=[True, False]
    ).head(10)

    st.dataframe(
        fastest_routes,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Bottom 10 Slowest Factory-to-State Routes")

    slowest_routes = route_summary.sort_values(
        ["Average_Lead_Time", "Orders"],
        ascending=[False, False]
    ).head(10)

    st.dataframe(
        slowest_routes,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("All Factory-to-State Routes")

    st.dataframe(
        route_summary.sort_values("Average_Lead_Time"),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No route data available for the selected filters.")


# --------------------------------------------------
# 11. GEOGRAPHIC SHIPPING MAP
# --------------------------------------------------

st.divider()
st.header("Geographic Shipping Performance")

st.caption(
    "Average order-to-ship interval by US state. "
    "States without recognized codes or matching records may not appear."
)

map_data = (
    valid_lead.dropna(subset=["State_Code"])
    .groupby("State_Code", as_index=False)
    .agg(
        Average_Lead_Time=("Lead Time", "mean"),
        Orders=("Order ID", "nunique")
    )
)

if not map_data.empty:
    fig_map = px.choropleth(
        map_data,
        locations="State_Code",
        locationmode="USA-states",
        color="Average_Lead_Time",
        scope="usa",
        hover_name="State_Code",
        hover_data={
            "Average_Lead_Time": ":.1f",
            "Orders": True
        },
        color_continuous_scale="Oranges",
        labels={
            "Average_Lead_Time": "Avg Lead Time (Days)",
            "Orders": "Orders"
        },
        title="Average Order-to-Ship Interval by State"
    )

    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("No recognized US state codes found for the selected filters.")


# --------------------------------------------------
# 12. ROUTE DRILL-DOWN
# --------------------------------------------------

st.divider()
st.header("Route Drill-Down")

if not route_summary.empty:
    drill_factory = st.selectbox(
        "Choose Factory",
        sorted(route_summary["Factory"].dropna().unique())
    )

    factory_routes = route_summary[
        route_summary["Factory"] == drill_factory
    ]

    available_drill_states = sorted(
        factory_routes["State/Province"].dropna().unique()
    )

    if available_drill_states:
        drill_state = st.selectbox(
            "Choose Customer State",
            available_drill_states
        )

        drill_route = valid_lead[
            (valid_lead["Factory"] == drill_factory)
            & (valid_lead["State/Province"] == drill_state)
        ].copy()

        if not drill_route.empty:
            drill_orders = drill_route["Order ID"].nunique()
            drill_avg = drill_route["Lead Time"].mean()

            drill_delay_count = drill_route.loc[
                drill_route["Lead Time"] > threshold, "Order ID"
            ].nunique()

            drill_delay_pct = (
                drill_delay_count / drill_orders * 100 if drill_orders else 0
            )

            d1, d2, d3 = st.columns(3)
            d1.metric("Route Orders", f"{drill_orders:,}")
            d2.metric("Average Lead Time", f"{drill_avg:.1f} days")
            d3.metric("Delay Frequency", f"{drill_delay_pct:.2f}%")

            st.subheader("Selected Route Shipment Timeline")

            drill_cols = [
                "Order ID",
                "Order Date",
                "Ship Date",
                "Lead Time",
                "Ship Mode",
                "City",
                "State/Province",
                "Product Name"
            ]

            st.dataframe(
                drill_route[drill_cols].sort_values("Order Date"),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No orders found for this route.")
    else:
        st.info("No customer states available for the selected factory.")
else:
    st.info("No routes available to drill down.")


# --------------------------------------------------
# 13. ORDER-LEVEL SHIPMENT TIMELINE
# --------------------------------------------------

st.divider()
st.subheader("Order-level Shipment Timeline")

timeline_cols = [
    "Order ID",
    "Order Date",
    "Ship Date",
    "Lead Time",
    "Factory",
    "State/Province",
    "Ship Mode"
]

st.dataframe(
    filtered[timeline_cols].sort_values("Order Date"),
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 14. DATA QUALITY NOTE
# --------------------------------------------------

st.divider()
st.subheader("Data Quality Note")

st.warning(
    "Lead Time is calculated as Ship Date minus Order Date. "
    "It measures the order-to-ship interval, not actual delivery transit time. "
    "Negative intervals are excluded from lead-time analysis. Validate unusual "
    "date differences before drawing operational conclusions."
)


# --------------------------------------------------
# 15. DOWNLOAD FILTERED DATA
# --------------------------------------------------

st.divider()
st.subheader("Download Filtered Data")

csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Data as CSV",
    data=csv_data,
    file_name="Nassau_Candy_Filtered_Data.csv",
    mime="text/csv"
)


# --------------------------------------------------
# 16. KEY FINDINGS & CONCLUSION
# --------------------------------------------------

st.divider()
st.subheader("Key Findings")

st.markdown("""
- **Shipping Analysis:** Compare average order-to-ship intervals across ship modes.
- **Factory Performance:** Review sales and delay frequency by factory.
- **Regional Analysis:** Explore average order-to-ship intervals across regions and states.
- **Route Analysis:** Compare order volume, average lead time, variability, and relative efficiency scores.
- **Interactive Analysis:** Use sidebar filters and the threshold slider to investigate different parts of the dataset.
""")

st.subheader("Project Conclusion")

st.markdown("""
This dashboard provides an interactive view of Nassau Candy Distributor's sales,
factory performance, and order-to-ship intervals.

It supports comparisons across shipping methods, factories, regions, states, and
factory-to-state routes. The calculated lead time represents the interval between
order date and ship date, not actual delivery transit time. Unusual date differences
and geographic field formats should be validated before making operational decisions.
""")