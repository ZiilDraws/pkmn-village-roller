# pkmn-village-roller
Does the boring tedious work of a pokemon village moderator

Requires Google Service Account credentials with Google Sheets API access. Tutorial below.

Currently set up for the fake mastersheet. 


## TUTORIAL TO SET UP SHEETS API ACCESS (REQUIRED)

### 1. Go to the Google Cloud Platform Console:
Open your web browser and go to the Google Cloud Platform Console.

If you're not already signed in to your Google account, sign in with your credentials.

### 2. Create a new project:
Click on the project drop-down and select "New Project".

Enter a name for your project and click on the "Create" button.

### 3. Enable the Google Sheets API:
In the left sidebar, click on "APIs & Services" and then "Library".

In the search bar, type "Google Sheets API" and select the API from the search results.

Click on the "Enable" button to enable the API for your project.

### 4. Set up credentials:
In the left sidebar, click on "APIs & Services" and then "Credentials".

Click on the "Create Credentials" button and select "Service Account".

Enter a name for your service account and click on the "Create" button.

Clock "Done", we do not use the optional options.

Press your service account email. (This is the email you need for step 5, so make sure to copy it to somewhere for the time being)

Select "Keys"

In the "Add Key/Create new key" section, select the JSON key type and click on the "Create" button.

A JSON file containing your credentials will be downloaded to your computer.

Rename this file to credentials.json and place it in a folder called "env" next to the files from this program.

### 5. Share the Google Sheets folder:
THIS IS ONLY NECCESSARY (and only possible) WHEN PROGRAM IS OUT OF PRE-RELEASE

Open sharing for the Drive folder containing all member sheets.

Enter the email address associated with the service account you created in step 4.

Set the access level for the service account to allow it to read or edit the document as desired.

Click on the "Send" button to share the document with the service account.

### 6. Done:
Have a nice time having a nicer time rolling. 
