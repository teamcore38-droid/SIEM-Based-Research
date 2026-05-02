"""
Alert Grouping Analysis
Groups related alerts into attack campaigns
"""

import pandas as pd
import matplotlib.pyplot as plt
import pickle
import os

def analyze_alert_grouping():
    """
    Analyze how alerts are grouped into campaigns
    """
    
    print("="*75)
    print("🔗 ALERT GROUPING ANALYSIS")
    print("="*75)
    
    # Load predictions with results
    print("\n📂 Loading predictions data...")
    df = pd.read_csv('../../data/processed/predictions_with_results.csv')
    print(f"   ✅ Loaded {len(df):,} samples")
    
    # Filter only attack traffic (attack_type != 'normal')
    print("\n🔍 Filtering attack traffic...")
    attack_df = df[df['attack_type'] != 'normal'].copy()
    print(f"   ✅ Attack samples: {len(attack_df):,}")
    print(f"   ✅ Normal samples: {(df['attack_type'] == 'normal').sum():,}")
    
    if len(attack_df) == 0:
        print("\n❌ No attack samples found!")
        return
    
    # Check if group_id exists
    if 'group_id' not in attack_df.columns or attack_df['group_id'].isna().all():
        print("\n⚠️  Warning: No group_id found in data")
        print("   Creating groups based on campaign_id...")
        
        # Use campaign_id as group identifier
        if 'campaign_id' in attack_df.columns:
            attack_df['group_id'] = attack_df['campaign_id']
        else:
            print("❌ No campaign_id found either!")
            return
    
    # Remove NaN groups
    grouped = attack_df[attack_df['group_id'].notna()].copy()
    
    if len(grouped) == 0:
        print("\n❌ No valid groups found!")
        return
    
    # Load encoders
    print("\n🔄 Loading label encoders...")
    try:
        with open('../../models/label_encoders.pkl', 'rb') as f:
            encoders = pickle.load(f)
        print("   ✅ Encoders loaded")
    except FileNotFoundError:
        print("❌ Encoders not found! Run 02_preprocess_data.py first")
        return
    
    # Group statistics
    print("\n📊 Calculating group statistics...")
    
    n_groups = grouped['group_id'].nunique()
    avg_size = len(grouped) / n_groups
    
    group_sizes = grouped.groupby('group_id').size()
    max_size = group_sizes.max()
    min_size = group_sizes.min()
    
    print(f"\n✅ Alert Grouping Statistics:")
    print(f"   Total attack alerts: {len(attack_df):,}")
    print(f"   Grouped alerts: {len(grouped):,}")
    print(f"   Number of groups: {n_groups}")
    print(f"   Average group size: {avg_size:.2f} alerts")
    print(f"   Largest group: {max_size} alerts")
    print(f"   Smallest group: {min_size} alerts")
    
    # Alert reduction
    reduction_pct = ((len(attack_df) - n_groups) / len(attack_df)) * 100
    print(f"\n   🎯 Alert Reduction: {reduction_pct:.1f}%")
    print(f"      Security analysts see {n_groups} groups")
    print(f"      instead of {len(attack_df):,} individual alerts!")
    
    # Group by attack type
    print("\n📊 Analyzing groups by attack type...")
    
    # Count by attack type
    attack_type_groups = grouped.groupby('attack_type').agg({
        'group_id': 'nunique',
        'alert_id': 'count'
    }).rename(columns={'group_id': 'num_groups', 'alert_id': 'num_alerts'})
    
    attack_type_groups['avg_alerts_per_group'] = (
        attack_type_groups['num_alerts'] / attack_type_groups['num_groups']
    )
    
    print("\n   Attack Type Summary:")
    print(attack_type_groups.to_string())
    
    # Create results directory
    print("\n📊 Creating visualizations...")
    os.makedirs('../../results', exist_ok=True)
    
    # ========================================
    # PLOT 1: Group size distribution
    # ========================================
    plt.figure(figsize=(12, 6))
    plt.hist(group_sizes, bins=30, color='steelblue', edgecolor='black')
    plt.axvline(avg_size, color='red', linestyle='--', linewidth=2,
               label=f'Average: {avg_size:.2f}')
    plt.xlabel('Alerts per Group', fontsize=12)
    plt.ylabel('Number of Groups', fontsize=12)
    plt.title('Distribution of Alert Group Sizes\n(Alert Grouping Module)', 
              fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('../../results/07_group_size_distribution.png', dpi=300, bbox_inches='tight')
    print("   ✅ Saved: results/07_group_size_distribution.png")
    plt.close()
    
    # ========================================
    # PLOT 2: Attacks by ward and type
    # ========================================
    ward_attack = pd.crosstab(
        grouped['ward'], 
        grouped['attack_type']
    )
    
    plt.figure(figsize=(14, 8))
    ward_attack.plot(kind='bar', stacked=True, ax=plt.gca(), colormap='Set3')
    plt.title('Attack Distribution by Ward and Type\n(Shows where attacks occur)', 
              fontsize=14, fontweight='bold')
    plt.xlabel('Ward', fontsize=12)
    plt.ylabel('Number of Alerts', fontsize=12)
    plt.legend(title='Attack Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('../../results/08_attacks_by_ward_detailed.png', dpi=300, bbox_inches='tight')
    print("   ✅ Saved: results/08_attacks_by_ward_detailed.png")
    plt.close()
    
    # ========================================
    # PLOT 3: Top 20 largest groups
    # ========================================
    top_groups = grouped.groupby('group_id').agg({
        'alert_id': 'count',
        'attack_type': 'first',
        'ward': 'first'
    }).sort_values('alert_id', ascending=False).head(20)
    
    plt.figure(figsize=(14, 8))
    colors = plt.cm.Set3(range(len(top_groups)))
    bars = plt.barh(range(len(top_groups)), top_groups['alert_id'], color=colors)
    
    # Create labels with attack type and ward
    labels = [f"{row['attack_type']}\n({row['ward']})" 
              for idx, row in top_groups.iterrows()]
    
    plt.yticks(range(len(top_groups)), labels)
    plt.xlabel('Number of Alerts', fontsize=12)
    plt.title('Top 20 Largest Attack Campaigns\n(Coordinated attacks with most alerts)', 
              fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig('../../results/09_top_attack_campaigns.png', dpi=300, bbox_inches='tight')
    print("   ✅ Saved: results/09_top_attack_campaigns.png")
    plt.close()
    
    # ========================================
    # PLOT 4: Attack type distribution
    # ========================================
    attack_counts = grouped['attack_type'].value_counts()
    
    plt.figure(figsize=(12, 6))
    colors_pie = plt.cm.Set3(range(len(attack_counts)))
    plt.pie(attack_counts, labels=attack_counts.index, autopct='%1.1f%%',
            colors=colors_pie, startangle=90)
    plt.title('Attack Type Distribution\n(Proportion of each attack type)', 
              fontsize=14, fontweight='bold')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('../../results/10_attack_type_distribution.png', dpi=300, bbox_inches='tight')
    print("   ✅ Saved: results/10_attack_type_distribution.png")
    plt.close()
    
    # ========================================
    # Save grouping summary
    # ========================================
    print("\n💾 Creating grouping summary report...")
    
    summary_lines = []
    summary_lines.append("="*75)
    summary_lines.append("ALERT GROUPING ANALYSIS SUMMARY")
    summary_lines.append("="*75)
    summary_lines.append(f"\nGenerated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_lines.append("\n" + "="*75)
    summary_lines.append("OVERALL STATISTICS")
    summary_lines.append("="*75)
    summary_lines.append(f"Total Attack Alerts:     {len(attack_df):,}")
    summary_lines.append(f"Grouped Alerts:          {len(grouped):,}")
    summary_lines.append(f"Number of Groups:        {n_groups}")
    summary_lines.append(f"Average Group Size:      {avg_size:.2f} alerts")
    summary_lines.append(f"Largest Group:           {max_size} alerts")
    summary_lines.append(f"Smallest Group:          {min_size} alerts")
    summary_lines.append(f"Alert Reduction:         {reduction_pct:.1f}%")
    
    summary_lines.append("\n" + "="*75)
    summary_lines.append("GROUPS BY ATTACK TYPE")
    summary_lines.append("="*75)
    summary_lines.append(attack_type_groups.to_string())
    
    summary_lines.append("\n" + "="*75)
    summary_lines.append("TOP 10 LARGEST CAMPAIGNS")
    summary_lines.append("="*75)
    for idx, (group_id, row) in enumerate(top_groups.head(10).iterrows(), 1):
        summary_lines.append(f"{idx:2d}. {group_id}: {row['alert_id']} alerts "
                            f"({row['attack_type']}, {row['ward']})")
    
    summary_lines.append("\n" + "="*75)
    summary_lines.append("ALERT REDUCTION BENEFIT")
    summary_lines.append("="*75)
    summary_lines.append(f"Without Grouping: Security team sees {len(attack_df):,} individual alerts")
    summary_lines.append(f"With Grouping:    Security team sees {n_groups} grouped campaigns")
    summary_lines.append(f"Time Saved:       {reduction_pct:.1f}% fewer alerts to review")
    summary_lines.append(f"")
    summary_lines.append(f"Example: Instead of reviewing {len(attack_df):,} alerts manually,")
    summary_lines.append(f"analysts can focus on {n_groups} coordinated attack campaigns.")
    
    summary_path = '../../results/alert_grouping_summary.txt'
    with open(summary_path, 'w') as f:
        f.write('\n'.join(summary_lines))
    
    print(f"   ✅ Summary saved: {summary_path}")
    
    # ========================================
    # Save grouped alerts CSV for Basheer
    # ========================================
    print("\n💾 Creating CSV output for Basheer (Incident Correlation)...")
    
    # Add group statistics to each alert
    group_stats = grouped.groupby('group_id').agg({
        'alert_id': 'count',
        'predicted_priority': lambda x: x.mode()[0] if len(x) > 0 else 'MEDIUM'
    }).rename(columns={
        'alert_id': 'alerts_in_group',
        'predicted_priority': 'group_priority'
    })
    
    grouped_with_stats = grouped.merge(
        group_stats, 
        left_on='group_id', 
        right_index=True, 
        how='left'
    )
    
    # Save for Basheer
    basheer_output = '../../data/processed/grouped_alerts_for_correlation.csv'
    grouped_with_stats.to_csv(basheer_output, index=False)
    print(f"   ✅ Saved: {basheer_output}")
    print(f"   📊 {len(grouped_with_stats):,} alerts in {n_groups} groups")
    
    # Final summary
    print("\n" + "="*75)
    print("✅ ALERT GROUPING ANALYSIS COMPLETE!")
    print("="*75)
    print(f"\n📊 Results Summary:")
    print(f"   • 4 visualization charts created")
    print(f"   • 1 summary report generated")
    print(f"   • 1 CSV file for Basheer's component")
    print(f"\n🎯 Alert Reduction: {reduction_pct:.1f}%")
    print(f"   Security team workload reduced from {len(attack_df):,} to {n_groups} items!")
    print(f"\n📁 Check results/ folder for all outputs\n")


if __name__ == "__main__":
    try:
        analyze_alert_grouping()
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()