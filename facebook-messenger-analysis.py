#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 13:18:02 2020

@author: matthew-bailey
"""

from bs4 import BeautifulSoup
from datetime import datetime
from collections import Counter, defaultdict
import re
import os
import matplotlib.pyplot as plt
import random


AUTHOR_TO_NICKNAME = {"Matthew Collyer": ["You", "Matthew Collyer", "Latent Lesbian Vampirism"],
                      "Anna Mowbray": ["You", "Anna Mowbray", "Spongey Maternal Fat Deposit"],
                      "Tim Wallis": ["You", "Tim Wallis", "Mad Spermatic Bubbles Endlessly Spilling out Kanye"],
                      "Fraser Boistelle": ["You", "Fraser Boistelle", "One Second Late"],
                      "Sarah Goodenough": ["You", "Sarah Goodenough", "Ifishy that's even your real name"],
                      "Alastair Carr": ["You", "Alastair Carr", "Squint Dust"],
                      "Matt Bailey": ["You", "Matt Bailey", "A Subtle Facist"],
                      "Tom Britton": ["You", "Tom Britton", "Scared by a ventriloquist"],
                      "Oscar Arnstein": ["You", "Oscar Arnstein", "Spoon Twat"],
                      "Daisy Deller": ["You", "Daisy Deller"],
                      "Jay Alice": ["You", "Jay Alice", "Jasmine White"]}
                      
MESSAGE_CLASS = "pam _3-95 _2pi0 _2lej uiBoxWhite noborder"
AUTHOR_CLASS = "_3-96 _2pio _2lek _2lel"
TIME_CLASS = "_3-94 _2lem"
CONTENT_CLASS = "_3-96 _2let"
REACTION_CLASS = "_tqp"

SWEARWORDS = ("fuck", "shit", "piss", "cunt",
              "bastard", "bollocks", "bloody", "damn",
              "boaby", "dobber", "bawbag")

def string_to_onlyalpha(string):
    """
    Get only alphanumeric characters from a string.
    
    Replace hyphens with spaces so as to not mangle hyphenated words, and replace apostrophes with blanks to merge words like it's -> its, othewise we lose the ts.
    """
    string.replace("-", " ")
    string.replace("'", "")
    valids = re.sub(r"[^A-Za-z ]+", ' ', string)
    return valids.lower()
    
def string_to_onlyascii(string):
    """
    Filter out emoji and non-printable characters.
    """
    valids = [item for item in string if item.isascii() and item.isprintable()]
    return "".join(valids)

def get_words(string):
    """
    Extract individual words from a string.
    
    Discard blank words, and URLs
    """
    all_words = [item.strip() for item in string.split(" ") if item]
    all_words = [item for item in all_words if len(item) >= 2 or item in {"i", "a"}]
    return [item for item in all_words if not item.startswith("http") or not item.startswith("www")]

class FacebookMessage:
    def __init__(self, bs_soup):
        self.time = self.extract_time(bs_soup)
        self.author = self.extract_author(bs_soup)
        self.content = self.extract_content(bs_soup)
        if self.content:
            self.content = self.clean_content(self.content)
            
        self.reactions = self.extract_reactions(bs_soup)
        
    def is_valid(self):
        """
        Check we've got all the valid fields for this message.
        
        Return True is time, author and content are all available.
        """
        return (self.time is not None
              and self.author is not None
              and self.content is not None)
        
    @staticmethod
    def extract_time(bs_soup):
        """
        Extract the time this message was sent.
        
        Return None if we can't find a time.
        """
        sub_item = bs_soup.find("div", class_=TIME_CLASS).text
        
        if sub_item:
            return datetime.strptime(sub_item, "%d %b %Y, %H:%M")
        return None
 
    @staticmethod
    def extract_author(bs_soup):
        """
        Extract the time this message was sent.
        
        Return None if we can't find a time.
        """
        sub_item = bs_soup.find("div", class_=AUTHOR_CLASS)
        if sub_item:
            return sub_item.text
        return None
    
    @staticmethod
    def extract_content(bs_soup):
        sub_item = bs_soup.find("div", class_=CONTENT_CLASS)
        if sub_item:
            child = sub_item.div.findChildren("div" , recursive=False)[1]
            return child.text
        return None
   
    @staticmethod
    def clean_content(content):
        """
        Strip whitespace from either side of the content.
        """
        content = content.strip()
        return content
    
    @staticmethod
    def extract_reactions(bs_soup):
        """
        Extract reactions to this message.
        
        Returns a dict, keyed by reaction, with entries being a list of authors.
        """
        sub_item = bs_soup.find("ul", class_=REACTION_CLASS)
        if sub_item is None:
            return {}
        reactions = [child.text for child in sub_item.find_all("li")]
        react_dict = {reaction[0]: [] for reaction in reactions}
        for reaction in reactions:
            react_dict[reaction[0]].append(reaction[1:])
        return react_dict
    
    def is_special_message(self):
        """
        Return if this is a nickname or group chat name change.
        
        This is truly horrible, and misses a number of messages.
        """
        if not self.is_valid():
            return False
            
        # TODO: what if the author is wrong? then these don't match at all!
        for nickname in AUTHOR_TO_NICKNAME[self.author]:
        
            if self.content == f"{nickname} changed the chat theme.":
                return True
                
            if self.content == f"{nickname} joined the video chat.":
                return True
            
            if self.content == f"{nickname} joined the call.":
                return True
            
            if self.content.startswith(f"{nickname} named the group"):
                return True
                
            if self.content == f"{nickname} removed the group name.":
                return True
            
            if self.content == f"{nickname} sent a link.":
                return True
            
            if self.content == f"{nickname} sent an attachment.":
                return True
            
            if self.content.startswith(f"{nickname} set the emoji to"):
                return True
            
            if self.content.startswith(f"{nickname} set the nickname for "):
                return True
    
            if self.content == f"{nickname} changed the group photo.":
                return True
            
            if self.content.startswith(f"{nickname} added ") and self.content.endswith(" to the group."):
                return True
            
            if self.content.startswith(f"{nickname} removed ") and self.content.endswith(" from the group."):
                return True

            if self.content.startswith(f"{nickname} cleared the nickname for "):
                return True
            
            if self.content == f"{nickname} started a video chat.":
                return True
                
            if self.content == f"{nickname} left the group.":
                return True
        return False
    
def count_word_usage(counters_by_author, word_list):
    """
    Count each usage of a word in word_list, by author.
    """
    specific_word_counter = {}
    for author in counters_by_author.keys():
        word_counter = Counter()
        for item in counters_by_author[author]:
            for word in word_list:
                if word in item:
                    print(item)
                    word_counter[word] += counters_by_author[author][item]
        specific_word_counter[author] = word_counter
    return specific_word_counter

def get_all_messages(filenames):
    """
    Turn a list of filenames into facebook messages.
    """
    messages = []
    for filename in filenames:
        with open(filename, "r") as fi:
            soup = BeautifulSoup(fi, 'html.parser')
            for item in soup.find_all("div", class_=MESSAGE_CLASS):
                message = FacebookMessage(item)
                if not message.is_valid():
                    continue
                if message.is_special_message():
                    continue
                messages.append(message)
    return messages

def generate_activity_histogram(messages, filename):
    """
    Save a graph to filename of the times messages were sent.
    """
    times = range(24)
    fig, ax = plt.subplots()
    ax.hist([message.time.hour for message in messages], times, density=True)
    ax.set_xlabel("Time")
    ax.set_xlim(min(times), max(times))
    ax.set_xticks(times)
    ax.set_xticklabels(f"{item}" for item in times)
    ax.set_ylabel("Messages / Total Messages")
    ax.set_ylim(0, 0.2)
    fig.savefig(filename)
    plt.close(fig)
    
def get_word_counts(messages_by_author):
    """
    Count all the unique words and the number of times they're used, by author.
    """
    counters_by_author = {}
    for author in messages_by_author.keys():
        author_counter = Counter()
        for message in messages_by_author[author]:
            author_counter += Counter(get_words(string_to_onlyalpha(message.content)))
        counters_by_author[author] = author_counter
    return counters_by_author

def main():
    filenames = []
    for root, _, files  in os.walk("./"):
        for item in files:
            if item.endswith("html"):
                filenames.append(os.path.join(root, item))

    messages = get_all_messages(filenames)
    all_authors = sorted(list(set(message.author for message in messages)))
    
    os.makedirs("./Processed/", exist_ok=True)
    os.makedirs("./Graphs/", exist_ok=True)
    messages_by_author = {author: [message for message in messages
                                   if message.author == author]
                          for author in all_authors}
    counters_by_author = get_word_counts(messages_by_author)
    for author, counter in counters_by_author.items():
        print(f"Writing out for {author}.")
        with open(f"./Processed/{author}.csv", "w") as fi:
            fi.write("Word, Count\n")
            for word, val in counter.most_common():
                fi.write(f"{word}, {val}\n")

    react_counter = defaultdict(Counter)
    for message in messages:
        if not message.reactions:
            continue
        for react in message.reactions.keys():
            react_counter[react] += Counter(message.reactions[react])
    with open('./Processed/Reactions.csv', "w") as fi:
        fi.write("React, " + ", ".join(author for author in all_authors) + "\n")
        for react in react_counter.keys():
            fi.write(f"{react}, " + ", ".join(str(react_counter[react][author]) for author in all_authors) + "\n")

    for author in all_authors:
        generate_activity_histogram(messages_by_author[author], f"./Graphs/{author} Activity.pdf")
    
    swear_counter_by_author = count_word_usage(counters_by_author, SWEARWORDS)
    
    with open("./Processed/Swears.csv", "w") as fi:
        fi.write("Author, " + ", ".join(swear for swear in SWEARWORDS) + "\n")
        for author in all_authors:
            fi.write(f"{author}, " + ", ".join(str(swear_counter_by_author[author][swear]) for swear in SWEARWORDS) + "\n")
    
    for message in messages_by_author["Matthew Collyer"]:
        if "piss" in message.content.lower():
            print(message.content)
    
    for author in all_authors:
        with open(f"./{author} Total.txt", "w") as fi:
            author_messages = messages_by_author[author]
            random.shuffle(author_messages)
            for message in author_messages:
                if message.content.strip() and message.is_valid() and not message.is_special_message():
                    fi.write(string_to_onlyascii(message.content) + " ")
        
if __name__ == "__main__":
    main()
