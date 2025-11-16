#!/usr/bin/env python3

"""
Soccer Betting Dashboard
========================
Streamlit web interface for viewing daily soccer betting reports
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import glob
import json
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="⚽ Soccer Betting Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

class SoccerDashboard:
    """Interactive dashboard for soccer betting reports"""
    
    def __init__(self):
        self.reports_dir = "output reports"
        
    def load_latest_reports(self):
        """Load the most recent reports"""
        
        # Get latest daily picks
        daily_picks_files = glob.glob(f"{self.reports_dir}/daily_picks_*.csv")
        high_conf_files = glob.glob(f"{self.reports_dir}/high_confidence_picks_*.csv")
        
        latest_daily = None
        latest_high_conf = None
        latest_date = None
        
        if daily_picks_files:
            latest_daily_file = max(daily_picks_files, key=os.path.getctime)
            latest_daily = pd.read_csv(latest_daily_file)
            # Extract date from filename
            filename = os.path.basename(latest_daily_file)
            date_str = filename.split('_')[-1].replace('.csv', '')
            latest_date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
        
        if high_conf_files:
            latest_high_conf_file = max(high_conf_files, key=os.path.getctime)
            latest_high_conf = pd.read_csv(latest_high_conf_file)
        
        return latest_daily, latest_high_conf, latest_date
    
    def load_backtest_data(self):
        """Load historical backtest data for analysis"""
        
        backtest_file = f"{self.reports_dir}/backtest_detailed_20240801_20250904.csv"
        if os.path.exists(backtest_file):
            return pd.read_csv(backtest_file)
        return None
    
    def create_picks_overview(self, daily_picks, high_conf_picks, date):
        """Create overview of today's picks"""
        
        st.header(f"📅 Soccer Betting Picks - {date}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if daily_picks is not None:
                st.metric("🎯 Main Strategy Picks", len(daily_picks))
            else:
                st.metric("🎯 Main Strategy Picks", 0)
        
        with col2:
            if high_conf_picks is not None:
                st.metric("🛡️ High Confidence Picks", len(high_conf_picks))
            else:
                st.metric("🛡️ High Confidence Picks", 0)
        
        with col3:
            if daily_picks is not None:
                avg_edge = daily_picks['edge_percent'].mean()
                st.metric("📈 Avg Edge", f"{avg_edge:.1f}%")
            else:
                st.metric("📈 Avg Edge", "N/A")
        
        with col4:
            if daily_picks is not None:
                avg_conf = daily_picks['confidence_percent'].mean()
                st.metric("🎪 Avg Confidence", f"{avg_conf:.1f}%")
            else:
                st.metric("🎪 Avg Confidence", "N/A")
    
    def display_main_picks(self, daily_picks):
        """Display main strategy picks"""
        
        if daily_picks is None or len(daily_picks) == 0:
            st.warning("No main strategy picks available")
            return
        
        st.subheader("🚀 Main Strategy Picks (High Edge)")
        
        # Add risk level color coding
        def get_risk_color(risk):
            if risk == "Low Risk":
                return "🟢"
            elif risk == "Medium Risk":
                return "🟡"
            else:
                return "🔴"
        
        # Format display dataframe
        display_df = daily_picks.copy()
        display_df['Risk'] = display_df['risk_level'].apply(lambda x: f"{get_risk_color(x)} {x}")
        display_df['Edge'] = display_df['edge_percent'].apply(lambda x: f"{x:.1f}%")
        display_df['Confidence'] = display_df['confidence_percent'].apply(lambda x: f"{x:.1f}%")
        display_df['Odds'] = display_df['odds'].apply(lambda x: f"{x:.2f}")
        display_df['Stake'] = display_df['recommended_stake_pct'].apply(lambda x: f"{x}%")
        
        # Select columns for display
        columns_to_show = [
            'kick_off', 'home_team', 'away_team', 'league', 'market', 
            'Odds', 'Edge', 'Confidence', 'Stake', 'Risk'
        ]
        
        st.dataframe(
            display_df[columns_to_show],
            use_container_width=True,
            hide_index=True
        )
    
    def display_high_confidence_picks(self, high_conf_picks):
        """Display high confidence picks"""
        
        if high_conf_picks is None or len(high_conf_picks) == 0:
            st.warning("No high confidence picks available")
            return
        
        st.subheader("🛡️ High Confidence Picks (Safe Bets)")
        
        # Format display dataframe
        display_df = high_conf_picks.copy()
        
        # Add safety level emoji
        def get_safety_emoji(safety):
            if "VERY_SAFE" in safety:
                return "🔒"
            elif "SAFE" in safety:
                return "🛡️"
            elif "MODERATELY" in safety:
                return "⚠️"
            else:
                return "❓"
        
        display_df['Safety'] = display_df['market_safety'].apply(lambda x: f"{get_safety_emoji(x)} {x.replace('_', ' ').title()}")
        display_df['American Odds'] = display_df['american_odds'].apply(lambda x: f"{x:+d}")
        
        # Select columns for display
        columns_to_show = [
            'kick_off', 'home_team', 'away_team', 'league', 'market',
            'odds', 'American Odds', 'confidence_percent', 'Safety', 'reasoning'
        ]
        
        st.dataframe(
            display_df[columns_to_show],
            use_container_width=True,
            hide_index=True
        )
    
    def create_market_analysis(self, daily_picks):
        """Create market analysis charts"""
        
        if daily_picks is None or len(daily_picks) == 0:
            return
        
        st.subheader("📊 Market Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Market distribution
            market_counts = daily_picks['market'].value_counts()
            fig_pie = px.pie(
                values=market_counts.values,
                names=market_counts.index,
                title="Picks by Market Type"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # League distribution
            league_counts = daily_picks['league'].value_counts()
            fig_bar = px.bar(
                x=league_counts.values,
                y=league_counts.index,
                orientation='h',
                title="Picks by League"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    def create_performance_dashboard(self, backtest_data):
        """Create performance analysis from backtest data"""
        
        if backtest_data is None:
            st.warning("No historical backtest data available")
            return
        
        st.subheader("📈 Historical Performance Analysis")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_bets = len(backtest_data)
        wins = backtest_data['bet_won'].sum()
        win_rate = (wins / total_bets) * 100
        total_profit = backtest_data['profit_loss'].sum()
        total_staked = backtest_data['stake'].sum()
        roi = (total_profit / total_staked) * 100
        
        with col1:
            st.metric("Total Bets", f"{total_bets:,}")
        with col2:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            st.metric("Total P&L", f"${total_profit:+,.2f}")
        with col4:
            st.metric("ROI", f"{roi:+.1f}%")
        
        # Performance by market
        st.subheader("🎯 Performance by Market")
        
        market_performance = backtest_data.groupby('market').agg({
            'bet_won': ['count', 'sum'],
            'profit_loss': 'sum',
            'stake': 'sum'
        }).round(2)
        
        market_stats = []
        for market in market_performance.index:
            total_bets = market_performance.loc[market, ('bet_won', 'count')]
            wins = market_performance.loc[market, ('bet_won', 'sum')]
            profit = market_performance.loc[market, ('profit_loss', 'sum')]
            stake = market_performance.loc[market, ('stake', 'sum')]
            
            win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
            roi = (profit / stake * 100) if stake > 0 else 0
            
            market_stats.append({
                'Market': market,
                'Total Bets': int(total_bets),
                'Win Rate (%)': round(win_rate, 1),
                'Profit/Loss ($)': round(profit, 2),
                'ROI (%)': round(roi, 1)
            })
        
        market_df = pd.DataFrame(market_stats).sort_values('ROI (%)', ascending=False)
        st.dataframe(market_df, use_container_width=True, hide_index=True)
        
        # Monthly performance chart
        st.subheader("📅 Monthly Performance Trend")
        
        backtest_data['date'] = pd.to_datetime(backtest_data['date'])
        backtest_data['month'] = backtest_data['date'].dt.to_period('M')
        
        monthly_performance = backtest_data.groupby('month').agg({
            'profit_loss': 'sum',
            'bet_won': ['count', 'sum']
        }).round(2)
        
        monthly_profit = monthly_performance['profit_loss']['sum']
        monthly_bets = monthly_performance[('bet_won', 'count')]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_profit.index.astype(str),
            y=monthly_profit.values,
            mode='lines+markers',
            name='Monthly Profit/Loss',
            line=dict(color='green' if monthly_profit.iloc[-1] > 0 else 'red')
        ))
        
        fig.update_layout(
            title='Monthly Profit/Loss Trend',
            xaxis_title='Month',
            yaxis_title='Profit/Loss ($)',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def run_dashboard(self):
        """Run the main dashboard"""
        
        st.title("⚽ Soccer Betting Dashboard")
        st.markdown("---")
        
        # Sidebar
        st.sidebar.title("🎛️ Dashboard Controls")
        
        # Load data
        daily_picks, high_conf_picks, latest_date = self.load_latest_reports()
        backtest_data = self.load_backtest_data()
        
        # Dashboard tabs
        tab1, tab2, tab3 = st.tabs(["📅 Today's Picks", "📊 Market Analysis", "📈 Historical Performance"])
        
        with tab1:
            if latest_date:
                self.create_picks_overview(daily_picks, high_conf_picks, latest_date)
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    self.display_main_picks(daily_picks)
                
                with col2:
                    self.display_high_confidence_picks(high_conf_picks)
            else:
                st.warning("No recent reports found. Run the daily report generator first.")
        
        with tab2:
            self.create_market_analysis(daily_picks)
        
        with tab3:
            self.create_performance_dashboard(backtest_data)
        
        # Footer
        st.markdown("---")
        st.markdown("🎯 **Soccer Betting Dashboard** | Updated automatically with daily reports")

# Run the dashboard
if __name__ == "__main__":
    dashboard = SoccerDashboard()
    dashboard.run_dashboard()