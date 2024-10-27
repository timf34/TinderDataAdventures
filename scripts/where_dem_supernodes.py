import json
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns


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
    """Create various visualizations of the popularity metrics."""
    # Set up the plotting style
    plt.style.use('default')  # Using default style instead of seaborn

    # Create a figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 15))

    # 1. Distribution of matches
    axes[0, 0].hist(df['total_matches'], bins=30, edgecolor='black')
    axes[0, 0].set_title('Distribution of Total Matches')
    axes[0, 0].set_xlabel('Number of Matches')
    axes[0, 0].set_ylabel('Frequency')

    # 2. Messages received vs matches scatter plot
    axes[0, 1].scatter(df['total_matches'], df['total_messages_received'], alpha=0.5)
    axes[0, 1].set_title('Messages Received vs Total Matches')
    axes[0, 1].set_xlabel('Total Matches')
    axes[0, 1].set_ylabel('Total Messages Received')

    # 3. Match rate by age grouping
    df['age_group'] = pd.cut(df['age'], bins=range(18, 61, 5))
    df_age_stats = df.groupby('age_group')['match_rate'].mean()
    df_age_stats.plot(kind='bar', ax=axes[1, 0])
    axes[1, 0].set_title('Average Match Rate by Age Group')
    axes[1, 0].set_xlabel('Age Group')
    axes[1, 0].set_ylabel('Match Rate')
    axes[1, 0].tick_params(axis='x', rotation=45)

    # 4. Response rate vs Messages sent
    axes[1, 1].scatter(df['total_messages_sent'], df['response_rate'], alpha=0.5)
    axes[1, 1].set_title('Response Rate vs Messages Sent')
    axes[1, 1].set_xlabel('Total Messages Sent')
    axes[1, 1].set_ylabel('Response Rate')

    plt.tight_layout()
    plt.savefig('popularity_analysis.png')
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

        # Export detailed data to CSV
        df.to_csv('user_popularity_analysis.csv', index=False)
        print("\nDetailed analysis has been exported to 'user_popularity_analysis.csv'")
        print("Visualizations have been saved as 'popularity_analysis.png'")

    except FileNotFoundError:
        print("Error: Could not find the JSON file. Please check the file path.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON file. Please check the file format.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()