import requests
import pandas as pd
import json
import os

# GitHub token and base URL
BASE_URL = 'https://api.github.com'
ACCESS_TOKEN = 'PLACEHOLDER_TOKEN'
headers = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

def get_users_in_city(city, min_followers):
    """Search GitHub users by city and minimum followers"""
    query = f'location:{city} followers:>{min_followers}'
    url = f'{BASE_URL}/search/users'
    params = {'q': query, 'per_page': 100}  # Fetch 100 users per page (max allowed by GitHub)
    
    users = []
    
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching users: {response.status_code}")
            break
        data = response.json()
        users.extend(data.get('items', []))
        
        # Check if there is a next page in the Link header
        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            break
    
    return users


def get_user_details(username):
    """Fetch user details"""
    url = f'{BASE_URL}/users/{username}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_user_repos(username):
    """Get repositories of a GitHub user with pagination"""
    repos = []
    url = f'{BASE_URL}/users/{username}/repos'
    params = {'per_page': 100, 'page': 1}  # Start from page 1, fetching 100 repos per page
    
    while len(repos) < 500:  # Stop after fetching 500 repos
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching repos for {username}: {response.status_code}")
            break
        
        data = response.json()
        repos.extend(data)
        
        if len(data) < 100:  # If less than 100 repos were returned, we are on the last page
            break
        
        params['page'] += 1  # Move to the next page
    
    return repos[:500]

def clean_company_name(company_name):
    """Clean up company names"""
    if company_name:
        company_name = company_name.strip().replace('@', '').upper()
    return company_name

def save_to_csv(users_data, repos_data):
    """Save data to CSV files"""
    # Save users to users.csv
    users_df = pd.DataFrame(users_data)
    users_df.to_csv('users.csv', index=False)
    
    # Save repositories to repositories.csv
    repos_df = pd.DataFrame(repos_data)
    repos_df.to_csv('repositories.csv', index=False)

def main():
    city = 'Hyderabad'
    min_followers = 50

    users = get_users_in_city(city, min_followers)
    users_data = []
    repos_data = []

    for user in users:
        user_details = get_user_details(user['login'])

        # print(type(user_details))
        
        if user_details:
            # Clean up and organize user data
            users_data.append({
                'login': user_details['login'],
                'name': user_details.get('name'),
                'company': clean_company_name(user_details.get('company')),
                'location': user_details.get('location'),
                'email': user_details.get('email'),
                'hireable': user_details.get('hireable'),
                'bio': user_details.get('bio'),
                'public_repos': user_details['public_repos'],
                'followers': user_details['followers'],
                'following': user_details['following'],
                'created_at': user_details['created_at']
            })
            
            # Fetch repositories
            repos = get_user_repos(user_details['login'])
            for repo in repos:
                repos_data.append({
                    'login': user_details['login'],
                    'full_name': repo['full_name'],
                    'created_at': repo['created_at'],
                    'stargazers_count': repo['stargazers_count'],
                    'watchers_count': repo['watchers_count'],
                    'language': repo.get('language'),
                    'has_projects': repo['has_projects'],
                    'has_wiki': repo['has_wiki'],
                    'license_name': repo['license']['name'] if repo['license'] else None
                })

    # Save data to CSV
    save_to_csv(users_data, repos_data)

if __name__ == '__main__':
    main()