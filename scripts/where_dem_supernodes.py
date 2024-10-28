import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


def load_data(file_path):
    """Load JSON data from file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def analyze_user_popularity(data):
    """
    Analyze user popularity based on matches and message interactions.
    Returns a DataFrame with popularity metrics.
    """
    user_stats = []

    for user_data in data:
        user_id = user_data.get('userId', 'unknown')

        # Get basic user info
        user_info = user_data.get('user', {})
        stats = {
            'user_id': user_id,
            'age': calculate_age(user_info.get('birthDate')),
            'gender': user_info.get('gender'),
            'education': user_info.get('education'),
            'city': user_info.get('cityName'),
            'country': user_info.get('country'),
            'has_instagram': user_info.get('instagram', False),
            'has_spotify': user_info.get('spotify', False),
            'account_age_days': calculate_account_age(user_info.get('createDate')),
        }

        # Count total matches
        matches = user_data.get('matches', {})
        stats['total_matches'] = sum(matches.values())

        # Messages received stats
        messages_received = user_data.get('messagesReceived', {})
        stats['total_messages_received'] = sum(messages_received.values())

        # Messages sent stats
        messages_sent = user_data.get('messagesSent', {})
        stats['total_messages_sent'] = sum(messages_sent.values())

        # Swipe stats
        swipe_likes = user_data.get('swipeLikes', {})
        swipe_passes = user_data.get('swipePasses', {})
        stats['total_likes_given'] = sum(swipe_likes.values())
        stats['total_passes_given'] = sum(swipe_passes.values())

        # Calculate conversation stats
        if 'conversations' in user_data:
            conversations = user_data['conversations']
            stats['total_conversations'] = len(conversations)

            # Count messages per conversation
            total_messages = sum(len(conv.get('messages', [])) for conv in conversations)
            stats['avg_messages_per_conversation'] = (
                total_messages / len(conversations) if conversations else 0
            )

            # Count conversations with >1 message (indicating engagement)
            engaging_convos = sum(1 for conv in conversations if len(conv.get('messages', [])) > 1)
            stats['engaging_conversation_ratio'] = (
                engaging_convos / len(conversations) if conversations else 0
            )

        # Calculate derived metrics
        if stats['total_likes_given'] + stats['total_passes_given'] > 0:
            stats['match_rate'] = (
                    stats['total_matches'] /
                    (stats['total_likes_given'] + stats['total_passes_given'])
            )
        else:
            stats['match_rate'] = 0

        stats['messages_per_match'] = (
            stats['total_messages_received'] / stats['total_matches']
            if stats['total_matches'] > 0 else 0
        )

        stats['response_rate'] = (
            stats['total_messages_received'] / stats['total_messages_sent']
            if stats['total_messages_sent'] > 0 else 0
        )

        user_stats.append(stats)

    return pd.DataFrame(user_stats)


def calculate_age(birth_date_str):
    """Calculate age from birth date string."""
    if not birth_date_str:
        return None
    try:
        from datetime import datetime
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        today = datetime.now()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        return age
    except:
        return None


def calculate_account_age(create_date_str):
    """Calculate account age in days."""
    if not create_date_str:
        return None
    try:
        from datetime import datetime
        create_date = datetime.strptime(create_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        days = (datetime.now() - create_date).days
        return days
    except:
        return None


def generate_popularity_report(df):
    """Generate a detailed popularity report with comprehensive statistics."""
    print("\n=== Tinder User Popularity Analysis ===\n")

    # Function to print stats for a metric
    def print_metric_stats(metric_name, series):
        print(f"\n{metric_name} Statistics:")
        print(f"  Mean: {series.mean():.2f}")
        print(f"  Median: {series.median():.2f}")
        print(f"  Std Dev: {series.std():.2f}")
        print(f"  Min: {series.min():.2f}")
        print(f"  Max: {series.max():.2f}")

    # Overall statistics
    print("Dataset Overview:")
    print(f"Total users analyzed: {len(df)}")

    # Print comprehensive stats for each key metric
    print_metric_stats("Matches", df['total_matches'])
    print_metric_stats("Match Rate", df['match_rate'])
    print_metric_stats("Messages Received per Match", df['messages_per_match'])
    print_metric_stats("Response Rate", df['response_rate'])
    print_metric_stats("Messages Sent", df['total_messages_sent'])
    print_metric_stats("Messages Received", df['total_messages_received'])

    # Age distribution
    print("\nAge Distribution:")
    print(f"  Mean Age: {df['age'].mean():.1f}")
    print(f"  Median Age: {df['age'].median():.1f}")
    print(f"  Std Dev Age: {df['age'].std():.1f}")

    # Top users in different categories
    print("\nTop 10 Most Popular Users by Matches:")
    print("(Showing: user_id, age, gender, city, total_matches, match_rate)")
    top_matches = df.nlargest(10, 'total_matches')[
        ['user_id', 'age', 'gender', 'city', 'total_matches', 'match_rate']
    ]
    print(top_matches.to_string(index=False))

    print("\nTop 10 Most Popular Users by Messages Received:")
    print("(Showing: user_id, age, gender, city, messages_received, messages_per_match)")
    top_messages = df.nlargest(10, 'total_messages_received')[
        ['user_id', 'age', 'gender', 'city', 'total_messages_received', 'messages_per_match']
    ]
    print(top_messages.to_string(index=False))

    print("\nTop 10 Users by Response Rate (minimum 50 messages sent):")
    print("(Showing: user_id, age, gender, city, response_rate, total_messages_sent)")
    response_rate = df[df['total_messages_sent'] >= 50].nlargest(10, 'response_rate')[
        ['user_id', 'age', 'gender', 'city', 'response_rate', 'total_messages_sent']
    ]
    print(response_rate.to_string(index=False))

    # Additional engagement statistics
    print("\nEngagement Statistics:")
    active_users = df[df['total_messages_sent'] > 0]
    print(f"  Active users (sent at least one message): {len(active_users)}")
    highly_active = df[df['total_messages_sent'] > df['total_messages_sent'].mean()]
    print(f"  Highly active users (above average messages sent): {len(highly_active)}")

    # Success rate statistics
    successful_users = df[df['response_rate'] > df['response_rate'].mean()]
    print("\nSuccess Rate Statistics:")
    print(f"  Users with above-average response rate: {len(successful_users)}")
    print(f"  Percentage of users with above-average success: {(len(successful_users) / len(df)) * 100:.1f}%")

    # Profile completeness correlation with success
    print("\nProfile Features Impact:")
    instagram_users = df[df['has_instagram'] == True]
    non_instagram_users = df[df['has_instagram'] == False]
    spotify_users = df[df['has_spotify'] == True]
    non_spotify_users = df[df['has_spotify'] == False]

    print("Instagram Impact:")
    print(f"  Users with Instagram - Mean match rate: {instagram_users['match_rate'].mean():.2%}")
    print(f"  Users without Instagram - Mean match rate: {non_instagram_users['match_rate'].mean():.2%}")

    print("Spotify Impact:")
    print(f"  Users with Spotify - Mean match rate: {spotify_users['match_rate'].mean():.2%}")
    print(f"  Users without Spotify - Mean match rate: {non_spotify_users['match_rate'].mean():.2%}")


def create_visualizations(df):
    """Create various visualizations of the popularity metrics with appropriate log scales."""
    # Set up the plotting style
    plt.style.use('default')

    # Create a figure with multiple subplots
    fig = plt.figure(figsize=(20, 15))

    # 1. Distribution of matches (log scale)
    ax1 = fig.add_subplot(221)
    matches_data = df['total_matches'][df['total_matches'] > 0]  # Filter out zeros for log scale
    if not matches_data.empty:
        ax1.hist(matches_data, bins=np.logspace(np.log10(matches_data.min()),
                                                np.log10(matches_data.max()), 50))
        ax1.set_xscale('log')
    ax1.set_title('Distribution of Total Matches (Log Scale)')
    ax1.set_xlabel('Number of Matches (Log Scale)')
    ax1.set_ylabel('Frequency')
    ax1.grid(True, which="both", ls="-", alpha=0.2)

    # 2. Messages received vs matches (log-log scale)
    ax2 = fig.add_subplot(222)
    mask = (df['total_matches'] > 0) & (df['total_messages_received'] > 0)
    if mask.any():
        ax2.scatter(df[mask]['total_matches'],
                    df[mask]['total_messages_received'],
                    alpha=0.5)
        ax2.set_xscale('log')
        ax2.set_yscale('log')
    ax2.set_title('Messages Received vs Total Matches (Log-Log Scale)')
    ax2.set_xlabel('Total Matches (Log Scale)')
    ax2.set_ylabel('Total Messages Received (Log Scale)')
    ax2.grid(True, which="both", ls="-", alpha=0.2)

    # 3. Match rate by age grouping (regular scale)
    ax3 = fig.add_subplot(223)
    df['age_group'] = pd.cut(df['age'], bins=range(18, 61, 5))
    df_age_stats = df.groupby('age_group', observed=True)['match_rate'].agg(['mean', 'median', 'std']).fillna(0)

    if not df_age_stats.empty:
        x = range(len(df_age_stats.index))
        ax3.bar([i - 0.2 for i in x], df_age_stats['mean'], 0.4,
                label='Mean', color='skyblue', alpha=0.7)
        ax3.bar([i + 0.2 for i in x], df_age_stats['median'], 0.4,
                label='Median', color='lightgreen', alpha=0.7)
        ax3.errorbar([i - 0.2 for i in x], df_age_stats['mean'],
                     yerr=df_age_stats['std'], fmt='none', color='black', alpha=0.3)
        ax3.set_xticks(x)
        ax3.set_xticklabels([str(interval) for interval in df_age_stats.index], rotation=45)

    ax3.set_title('Match Rate by Age Group')
    ax3.set_xlabel('Age Group')
    ax3.set_ylabel('Match Rate')
    ax3.legend()
    ax3.grid(True, alpha=0.2)

    # 4. Response rate vs Messages sent (log scale for messages)
    ax4 = fig.add_subplot(224)
    mask = (df['total_messages_sent'] > 0) & (df['total_matches'] > 0)
    if mask.any():
        matches_for_color = df[mask]['total_matches']
        vmin = max(1, matches_for_color.min())  # Ensure minimum is at least 1 for log scale
        vmax = matches_for_color.max()

        scatter = ax4.scatter(df[mask]['total_messages_sent'],
                              df[mask]['response_rate'],
                              alpha=0.5,
                              c=matches_for_color,  # Color by number of matches
                              cmap='viridis',
                              norm=LogNorm(vmin=vmin, vmax=vmax))
        ax4.set_xscale('log')
        plt.colorbar(scatter, ax=ax4, label='Number of Matches')

    ax4.set_title('Response Rate vs Messages Sent')
    ax4.set_xlabel('Total Messages Sent (Log Scale)')
    ax4.set_ylabel('Response Rate')
    ax4.grid(True, which="both", ls="-", alpha=0.2)

    # Add some additional useful statistics as text
    stats_text = (f"Median matches: {df['total_matches'].median():.0f}\n"
                  f"Median messages: {df['total_messages_sent'].median():.0f}\n"
                  f"Median response rate: {df['response_rate'].median():.2%}")
    plt.figtext(0.02, 0.02, stats_text, fontsize=10, bbox=dict(facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig('popularity_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()


def create_additional_visualizations(df):
    """Create additional visualizations focused on message patterns."""
    plt.figure(figsize=(15, 10))

    # 1. Messages sent distribution (log scale)
    plt.subplot(221)
    messages_sent = df['total_messages_sent'][df['total_messages_sent'] > 0]
    if not messages_sent.empty:
        plt.hist(messages_sent, bins=np.logspace(np.log10(messages_sent.min()),
                                                 np.log10(messages_sent.max()), 50))
        plt.xscale('log')
    plt.title('Distribution of Messages Sent (Log Scale)')
    plt.xlabel('Messages Sent (Log Scale)')
    plt.ylabel('Number of Users')

    # 2. Response rate distribution
    plt.subplot(222)
    response_rates = df['response_rate'][df['response_rate'] > 0]
    if not response_rates.empty:
        plt.hist(response_rates, bins=50)
    plt.title('Distribution of Response Rates')
    plt.xlabel('Response Rate')
    plt.ylabel('Number of Users')

    # 3. Messages per match distribution (log scale)
    plt.subplot(223)
    msgs_per_match = df['messages_per_match'][df['messages_per_match'] > 0]
    if not msgs_per_match.empty:
        plt.hist(msgs_per_match, bins=np.logspace(np.log10(msgs_per_match.min()),
                                                  np.log10(msgs_per_match.max()), 50))
        plt.xscale('log')
    plt.title('Distribution of Messages per Match (Log Scale)')
    plt.xlabel('Messages per Match (Log Scale)')
    plt.ylabel('Number of Users')

    # 4. Activity over time (for users with account age data)
    plt.subplot(224)
    mask = df['account_age_days'].notna() & (df['total_messages_sent'] > 0)
    if mask.any():
        plt.scatter(df[mask]['account_age_days'],
                    df[mask]['total_messages_sent'],
                    alpha=0.5)
        plt.yscale('log')
    plt.title('User Activity vs Account Age')
    plt.xlabel('Account Age (Days)')
    plt.ylabel('Total Messages Sent (Log Scale)')

    plt.tight_layout()
    plt.savefig('message_patterns.png', dpi=300, bbox_inches='tight')
    plt.close()


def main():
    file_path = '../data/tinder_profiles_2021-11-10.json'

    try:
        # Load and analyze data
        print("Loading and analyzing data...")
        data = load_data(file_path)
        df = analyze_user_popularity(data)

        # Generate report
        generate_popularity_report(df)

        # Create visualizations
        print("\nGenerating visualizations...")
        create_visualizations(df)
        create_additional_visualizations(df)

        # Export detailed data to CSV
        df.to_csv('user_popularity_analysis.csv', index=False)
        print("\nDetailed analysis has been exported to 'user_popularity_analysis.csv'")
        print("Visualizations have been saved as 'popularity_analysis.png' and 'message_patterns.png'")

    except FileNotFoundError:
        print("Error: Could not find the JSON file. Please check the file path.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON file. Please check the file format.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()