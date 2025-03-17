import json
from config import Config
import ckan_metadata_upload as ckan
import csv
import time
import logging
import ast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_contributors(contributors_string, max_contributors=10):
    # Check if it's already a list or empty
    if not contributors_string:
        return []
    
    if isinstance(contributors_string, list):
        return contributors_string[:max_contributors]  # Limit to max_contributors
    
    # Split by commas, but be careful with the formatting
    contributors_list = []
    
    # Simple split and strip to get individual contributors
    raw_contributors = [c.strip() for c in contributors_string.split(',')]
    
    # Add non-empty contributors until we reach the maximum
    for contributor in raw_contributors:
        if contributor:  # Skip empty strings
            contributors_list.append(contributor)
            if len(contributors_list) >= max_contributors:
                break  # Stop after reaching max_contributors
    
    return contributors_list

def get_description(row):
    """
    Get a proper description from the row. If the description is too short or a placeholder,
    use the first sentence from the detailed_description instead.
    
    Args:
        row (dict): A dictionary representing a row from the CSV
        
    Returns:
        str: The appropriate description to use
    """
    description = row.get('description', '')
    
    # Check if description is too short or is the default placeholder
    if len(description) < 20 or description == "No description provided":
        # Get detailed description
        detailed_description = row.get('detailed_description', '')
        
        if detailed_description:
            # Extract first sentence from detailed description
            import re
            # Match until the first period followed by a space or end of string
            match = re.search(r'^(.*?\.(\s|$))', detailed_description)
            if match:
                first_sentence = match.group(1).strip()
                return first_sentence
            else:
                # If no period found, return first 100 characters or the entire text if shorter
                return detailed_description[:min(100, len(detailed_description))]
    
    # Return original description if it's valid or if no alternative is found
    return description

def check_organization_exists(org_name):
    """
    Check if an organization exists in the CKAN instance
    """
    try:
        # Try to get the organization by name
        response = ckan.action('organization_show', {'id': org_name})
        return True
    except Exception as e:
        # If organization doesn't exist or there's any other error
        logger.warning(f"Organization {org_name} not found: {e}")
        return False


def format_contributors(contributors_data):
    try:
        # Try to parse the data if it's a string
        if isinstance(contributors_data, str):
            import json
            import ast
            try:
                contributors = json.loads(contributors_data)
            except json.JSONDecodeError:
                try:
                    contributors = ast.literal_eval(contributors_data)
                except (SyntaxError, ValueError):
                    return "Invalid contributor data format"
        else:
            contributors = contributors_data
            
        # Sort contributors by number of contributions (highest first)
        sorted_contributors = sorted(contributors, key=lambda x: x.get('contributions', 0), reverse=True)
        
        # Format the output with proper indentation and structure
        output_lines = ["## Contributors\n"]
        
        for i, contributor in enumerate(sorted_contributors):
            name = contributor.get('name', 'Unknown')
            username = contributor.get('username', '')
            contributions = contributor.get('contributions', 0)
            email = contributor.get('email', '')
            profile = contributor.get('profile_url', '')
            
            output_lines.append(f"### {i+1}. {name} (@{username})")
            output_lines.append(f"* Contributions: {contributions}")
            if email and email != "null":
                output_lines.append(f"* Email: {email}")
            if profile:
                output_lines.append(f"* GitHub: {profile}")
            output_lines.append("")  # Empty line between contributors
            
        return "\n".join(output_lines)
    except Exception as e:
        return f"Error formatting contributors: {str(e)}"


def json_to_markdown_table(data):
    # Define the table headers
    headers = ["Username", "Contributions", "Profile", "Email", "Name", "Role"]
    
    # Create the header row
    header_row = "| " + " | ".join(headers) + " |"
    
    # Create the separator row
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    
    # Process each data entry into table rows
    data_rows = []
    for d in data:
        row_values = [
            d['username'].replace("|", "\\|"),                          # Username as plain text
            str(d['contributions']).replace("|", "\\|"),                # Contributions as string
            f"[Profile]({d['profile_url']})".replace("|", "\\|"),       # Profile as a clickable link
            (d['email'] if d['email'] else "-").replace("|", "\\|"),    # Email or "-" if null
            (d['name'] if d['name'] else "-").replace("|", "\\|"),      # Name or "-" if null
            d['role'].replace("|", "\\|")                               # Role as plain text
        ]
        row_str = "| " + " | ".join(row_values) + " |"
        data_rows.append(row_str)
    
    # Combine all parts into the final table
    table = header_row + "\n" + separator_row + "\n" + "\n".join(data_rows)
    return table

if __name__ == '__main__':
    CSVFilePath = Config.get('metadata_filepath')

    
    with open(CSVFilePath, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            time.sleep(5)  # Rate limiting
            try:
                if row.get('resource_id'):
                    # Update existing resource metadata
                    resource_dict = {
                        'id': row['resource_id'],
                        'package_id': row['package_id'],
                        'name': row['resource_name'],
                        'description': row['description'],
                        'format': row['file_type'],
                        'url': row.get('url', '')
                    }
                    response = ckan.action('resource_patch', resource_dict)
                    
                elif row.get('package_id'):
                    # Create new resource metadata
                    resource_dict = {
                        'package_id': row['package_id'],
                        'name': row['resource_name'],
                        'description': row['description'],
                        'format': row['file_type'],
                        'url': row.get('url', '')
                    }
                    response = ckan.action('resource_create', resource_dict)
                    
                else:
                    if 'ckan_version' in row and isinstance(row['ckan_version'], str) and row['ckan_version'].startswith('['):
                        row['ckan_version'] = ast.literal_eval(row['ckan_version'])
                    # Create new dataset with metadata
                    extra_metadata = {'each_row_is': row.get('each_row_is', '')}
                    extras_list = [{'key': k, 'value': v} for k, v in extra_metadata.items()]
                    
                    tags_list = [{'name': tag.strip()} for tag in row['tags'].split(',')] if row.get('tags') else []
                    
                    # Get the GitHub organization name from the row
                    github_org_name = row.get('owner_org', '')

                    # Define the mapping from GitHub organization names to actual organization names
                    org_mapping = {
                        "datopian": "datopian",
                        "okfn": "okfn",
                        "DataShades": "link-digital",
                        "ckan": "ckan",
                        "keitaroinc": "keitaro",
                        "geosolutions-it": "geosolutions",
                        "NaturalHistoryMuseum": "natural-history-museum",
                        "ccca-dc": "climate-change-centre-austria",
                        "OpenGov-OpenData": "opengov",
                        "vrk-kpa": "finnish-digital-agency",
                        "qld-gov-au": "queensland-government",
                        "frictionlessdata": "frictionless-data",
                        "aptivate": "aptivate",
                        "GSA": "u-s-general-services-administration",
                        "TIBHannover": "technische-informationsbibliothek-tib",
                        "XVTSolutions": "xvt-solutions",
                        "CodeForAfrica": "code-for-africa-cfa",
                        "conwetlab": "conwet-lab",
                        "berlinonline": "berlinonline-gmbh",
                        "dpc-sdp": "single-digital-presence-department-of-government-services-victoria",
                        "datagovau": "data-gov-au",
                        "dathere": "dathere",
                        "open-data": "open-government-initiative-initiative-sur-le-gouvernement-ouvert",
                        "bcgov": "b-c-government"
                    }

                    # Convert the GitHub org name to the actual organization name
                    if github_org_name in org_mapping:
                        org_name = org_mapping[github_org_name]
                    else:
                        print(f"Organization '{github_org_name}' not found, using 'other' instead")
                        logger.info(f"Organization '{github_org_name}' not found, using 'other' instead")
                        org_name = 'other'
                    print(f"owner org reformatted to {org_name} from {github_org_name}")


                    # Process maintainer field - extract emails if it's in JSON format
                    maintainer_emails = ''
                    if row.get('maintainers'):
                        try:
                            # Try to parse as JSON
                            maintainers = json.loads(row['maintainers'])
                            if isinstance(maintainers, list):
                                emails = []
                                for maintainer in maintainers:
                                    if isinstance(maintainer, dict) and maintainer.get('email'):
                                        if maintainer['email'] != 'null' and maintainer['email']:
                                            emails.append(maintainer['email'])
                                maintainer_emails = ', '.join(emails)
                        except:
                            # If not JSON, use as-is
                            maintainer_emails = row.get('maintainers', '')

                    ##formatted_contributors = [{'name': contributor.strip()} for contributor in row['contributors'].split(',')] if row.get('contributors') else []
                    ##mainnames = [{'name': mainname.strip()} for mainname in row['maintainers_list'].split(',')] if row.get('maintainers_list') else []
                    formatted_contributors = format_contributors(row.get('contributor_details', ''))
                    contributors_data = row.get('contributors', '')
                    contributors_list = parse_contributors(contributors_data)

                    dataset_dict = {
                        'name': row.get('title', ''),  # URL slug
                        ##'contact_name' : mainnames,
                        'contact_name' : row.get('maintainers_list',''),
                        'contact_email' : maintainer_emails,
                        'title': row.get('title', ''),
                        'notes': get_description(row),
                        'detailed_info': row.get('detailed_description', ''),  # Description
                        'owner_org': org_name,
                        'license': row.get('license',''),
                        'tags': tags_list,
                        'url': row.get('github_url', ''),  # GitHub Repository URL
                        'extension_type': row.get('extension_type', ''),
                        'is_archived': row.get('is_archived', ''),
                        'archive_reason': row.get('archive_reason', ''),
                        'organization_url': row.get('organization_url', ''),
                        'language_stats': row.get('language_stats', ''),
                        'repository_size': row.get('repository_size', ''),
                        'forks_count': row.get('forks_count', ''),
                        'total_releases': row.get('total_releases', ''),
                        'latest_release': row.get('latest_release_version', ''),
                        'release_date': row.get('latest_release_date', ''),
                        'ckan_version': row.get('ckan_version', ''),
                        'stars': row.get('stars', ''),
                        'last_update': row.get('last_update', ''),
                        'open_issues': row.get('open_issues', ''),
                        'contributors_count': row.get('contributors_count', ''), 
                        ##'contributors': json_to_markdown_table(row.get('contributors')),
                        #'contributors': 'contrib1',
                        #'contributors': 'contrib2',
                        'contributors': contributors_list,
                        #'contributors': row.get('contributors', ''),
                        ##'contributor_details': formatted_contributors,
                        'contributor_details': row.get('contributor_details', ''),
                        'type': 'extension',
                        'group' : 'test'
                    }
                    #contribs = row.get('contributors', '')
                    #for i in range(row.get('contributors_count', '')):
                    #    contlist= contribs.split(", ")
                    #    dataset_dict = {'contributors': contlist[i]}
                    
                    # Remove any empty string values to avoid CKAN validation issues
                    dataset_dict = {k: v for k, v in dataset_dict.items() if v != ''}
                    
                    response = ckan.action('package_create', dataset_dict)
                    
                    # Create resource metadata if resource details are provided
                    if row.get('resource_name'):
                        resource_dict = {
                            'package_id': dataset_dict['name'],
                            'name': row['resource_name'],
                            'description': row.get('description', ''),
                            'format': row.get('file_type', ''),
                            'url': row.get('url', '')
                        }
                        response = ckan.action('resource_create', resource_dict)
                    
            except Exception as e:
                logger.error(f"Error processing row: {e}")
                logger.error(f"Failed row data: {row}")