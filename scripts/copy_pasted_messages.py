import json
from collections import defaultdict
import pandas as pd


def load_data(file_path):
    """Load JSON data from file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def analyze_repeated_messages(data):
    """
    Analyze messages that users have copy-pasted to multiple matches.
    Returns a DataFrame of repeated messages sorted by frequency and length.
    """
    # Dictionary to store messages by user: {user_id: {message: count}}
    user_messages = defaultdict(lambda: defaultdict(int))

    # First pass: Count how many times each user sent each message
    for user_data in data:
        user_id = user_data.get('userId', 'unknown')

        if 'conversations' in user_data:
            for conversation in user_data['conversations']:
                if 'messages' in conversation:
                    for message in conversation['messages']:
                        if message.get('from') == 'You' and message.get('message'):
                            msg_text = message['message'].replace('&rsquo;', "'").strip()
                            user_messages[user_id][msg_text] += 1

    # Second pass: Collect messages that were used multiple times
    repeated_messages = []

    for user_id, messages in user_messages.items():
        for message, count in messages.items():
            if count > 1:  # Message was used multiple times by this user
                repeated_messages.append({
                    'user_id': user_id,
                    'message': message,
                    'length': len(message),
                    'times_used': count
                })

    # Convert to DataFrame and sort
    if repeated_messages:
        df = pd.DataFrame(repeated_messages)
        return df.sort_values(by=['times_used', 'length'], ascending=[False, False])
    else:
        return pd.DataFrame(columns=['user_id', 'message', 'length', 'times_used'])

def print_analysis(df, min_length=10, top_n=50):
    """Print the analysis results, filtering out short messages."""
    if df.empty:
        print("No repeated messages found!")
        return

    # Filter out short messages
    df_filtered = df[df['length'] >= min_length].head(top_n)

    print(f"\nTop {top_n} Most Repeated Messages (minimum length: {min_length} characters)")
    print("=" * 80)

    for idx, row in df_filtered.iterrows():
        print(f"\nMessage {idx + 1}:")
        print(f"User ID: {row['user_id']}")
        print(f"Text: \"{row['message']}\"")
        print(f"Length: {row['length']} characters")
        print(f"Used {row['times_used']} times")
        print("-" * 40)


def main():
    # Replace with your JSON file path
    file_path = '../data/tinder_profiles_2021-11-10.json'

    try:
        # Load and process data
        print("Loading data...")
        data = load_data(file_path)

        print("Analyzing repeated messages...")
        analysis_df = analyze_repeated_messages(data)

        # Print detailed analysis
        print_analysis(analysis_df, min_length=10)

        # Export to CSV
        analysis_df.to_csv('repeated_messages_analysis.csv', index=False)
        print("\nFull analysis has been exported to 'repeated_messages_analysis.csv'")

        # Print summary statistics
        print("\nSummary Statistics:")
        print(f"Number of users with repeated messages: {len(analysis_df['user_id'].unique())}")
        print(f"Total number of different repeated messages: {len(analysis_df)}")
        print(f"Average uses per repeated message: {analysis_df['times_used'].mean():.2f}")

    except FileNotFoundError:
        print("Error: Could not find the JSON file. Please check the file path.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON file. Please check the file format.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()