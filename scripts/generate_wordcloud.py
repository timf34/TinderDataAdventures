import json
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
import string
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd


def load_data(file_path):
    """Load JSON data from file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def preprocess_text(text):
    """Clean and preprocess text."""
    # Download required NLTK data (uncomment first time)
    # nltk.download('punkt')
    # nltk.download('stopwords')

    # Convert to lowercase
    text = text.lower()

    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Tokenize
    tokens = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]

    # Remove numbers and short words
    tokens = [word for word in tokens if word.isalpha() and len(word) > 2]

    return tokens


def analyze_messages(data):
    """Extract and analyze messages from the data."""
    all_messages = []

    # Extract messages from conversations
    for user_data in data:
        if 'conversations' in user_data:
            for conversation in user_data['conversations']:
                if 'messages' in conversation:
                    for message in conversation['messages']:
                        if 'message' in message and message['message']:
                            # Clean HTML entities
                            msg_text = message['message'].replace('&rsquo;', "'")
                            all_messages.append(msg_text)

    # Combine all messages and preprocess
    all_text = ' '.join(all_messages)
    tokens = preprocess_text(all_text)

    return tokens


def create_word_frequency(tokens):
    """Create word frequency distribution."""
    freq_dist = FreqDist(tokens)
    return freq_dist


def plot_top_words(freq_dist, n=20):
    """Plot top N most common words."""
    plt.figure(figsize=(12, 6))
    freq_dist.plot(n, cumulative=False)
    plt.title(f'Top {n} Most Common Words in Tinder Messages')
    plt.xlabel('Words')
    plt.ylabel('Frequency')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def generate_wordcloud(tokens):
    """Generate and display word cloud."""
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        max_words=100
    ).generate(' '.join(tokens))

    plt.figure(figsize=(16, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud of Tinder Messages')
    plt.show()


def main():
    file_path = '../data/tinder_profiles_2021-11-10.json'

    try:
        # Load data
        data = load_data(file_path)

        # Analyze messages
        tokens = analyze_messages(data)

        # Get word frequencies
        freq_dist = create_word_frequency(tokens)

        # Print top 20 words and their frequencies
        print("\nTop 20 most common words:")
        for word, freq in freq_dist.most_common(20):
            print(f"{word}: {freq}")

        # Create visualizations
        plot_top_words(freq_dist)
        generate_wordcloud(tokens)

        # Export to CSV
        word_freq_df = pd.DataFrame(freq_dist.most_common(), columns=['Word', 'Frequency'])
        word_freq_df.to_csv('word_frequencies.csv', index=False)
        print("\nWord frequencies have been exported to 'word_frequencies.csv'")

    except FileNotFoundError:
        print("Error: Could not find the JSON file. Please check the file path.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON file. Please check the file format.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()