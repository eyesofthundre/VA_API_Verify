# VA API Verify

A tool that lets you look up information about U.S. military veterans — like whether someone is a verified veteran, what branch they served in, and what benefits they receive — by asking the U.S. Department of Veterans Affairs (VA) official database.

---

## What Does This Program Do?

Imagine the VA (the government office that helps military veterans) has a giant filing cabinet full of records about every person who ever served in the U.S. military. This program is like a special key that lets you open that filing cabinet and look things up — safely and officially.

You can ask questions like:
- "Is this person a verified veteran?" ✅ or ❌
- "What military branch did they serve in, and when?"
- "What disability rating do they have?"
- "What VA benefits are they enrolled in?"
- "Do they qualify for special programs like PACT Act?"

---

## Before You Start

### What You Will Need

Before anything else, make sure you have these things ready:

1. **A Mac computer** (this guide is written for Macs, especially MacBook Air M1)
2. **An internet connection**
3. **A VA API Key** — a special password from the VA that lets you use their system. You get this by signing up at the VA developer portal. Ask a grown-up or your organization's administrator to help you get one.
4. **A VA OAuth Token** — another special password for more detailed lookups. Same source as above.

> **What is an API?** An API (Application Programming Interface) is a way for computer programs to talk to each other. Think of it like a drive-through window: you place your order (your question), and the kitchen (the VA's computers) sends your food (the answer) back to you — all through a little window, without you going into the kitchen.

---

## Step 1 — Install the Tools Your Mac Needs

Your Mac needs a few helper programs installed before this will work. Follow each step carefully.

### Step 1a — Open the Terminal

The **Terminal** is a special app where you type commands to talk directly to your computer. It looks like a black (or white) window with blinking text.

1. Press the **Command key (⌘)** and the **Spacebar** at the same time. A search bar will appear at the top of your screen.
2. Type **Terminal** and press **Enter**.
3. A window will open that looks like this:

```
Last login: Mon Jan  1 12:00:00 on ttys000
YourName@MacBook ~ %
```

That blinking cursor after the `%` is where you will type your commands. Don't be scared — you can't break anything by reading this guide carefully!

### Step 1b — Install Homebrew (a helper that installs other helpers)

Homebrew is a free program that makes installing other programs on your Mac very easy. Think of it like an App Store, but for developer tools.

Copy and paste this entire line into your Terminal window, then press **Enter**:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

- It will ask for your Mac's **password** (the one you use to log in). Type it and press Enter — you won't see the letters as you type, and that's normal!
- This may take a few minutes. Wait until you see your prompt (`%`) come back.

> **Note for M1 Macs:** After Homebrew installs, it may print a message asking you to run two extra commands. Copy those commands from the Terminal and run them. They start with `echo` and `eval`.

### Step 1c — Install Python

Python is the programming language this project is written in. Your Mac may already have a version, but we want to make sure you have a good one.

```bash
brew install python
```

Wait for it to finish (you'll see the `%` come back), then verify it worked:

```bash
python3 --version
```

You should see something like `Python 3.12.0`. Any version starting with `3.9` or higher is fine.

### Step 1d — Download This Project

Now let's get the actual project files onto your computer. First, navigate to where you want to save it (your Desktop is a fine place):

```bash
cd ~/Desktop
```

Then download the project:

```bash
git clone https://github.com/YOUR_ORGANIZATION/VA_API_Verify.git
```

> Replace `YOUR_ORGANIZATION` with the actual GitHub path. If you received a `.zip` file instead, just unzip it to your Desktop.

Now go into the project folder:

```bash
cd VA_API_Verify
```

### Step 1e — Install the Project's Helper Libraries

This project needs a few small helper libraries (like `requests` for talking to the internet, and `rich` for making colorful output). Install them all at once:

```bash
pip3 install -r requirements.txt
```

You will see a lot of text scroll by. That's normal. Wait until the `%` comes back.

---

## Step 2 — Set Up Your Secret Keys

The program needs your VA API keys to work. We store them in a special file called `.env` (the dot at the beginning is on purpose — it means the file is hidden from normal view, for security).

### Creating the .env File

In your Terminal, make sure you are inside the `VA_API_Verify` folder (you can type `pwd` and press Enter to check — it should end with `/VA_API_Verify`).

Then run this command to open a simple text editor:

```bash
nano .env
```

A text editor will open inside your Terminal. Type the following, replacing the example values with your real keys:

```
VA_ENV=sandbox
VA_API_KEY=your_api_key_goes_here
VA_TOKEN=Bearer your_oauth_token_goes_here
```

Explanation of each line:
- `VA_ENV=sandbox` — Use the VA's test system (safe for learning; change to `production` when you're ready to look up real records)
- `VA_API_KEY=...` — Your key for the Veteran Confirmation API
- `VA_TOKEN=Bearer ...` — Your OAuth token for the detailed Verification API (the word `Bearer ` with a space must come before your actual token)

When done typing, press **Control + X**, then press **Y** when asked to save, then press **Enter**.

> **Security Note:** This `.env` file contains secret information. Never share it with anyone, and never send it in an email or chat message. The project is already set up to keep this file hidden from being accidentally uploaded online.

---

## Step 3 — Run the Program

Now the fun part! Let's look something up.

All commands start with:

```bash
python3 -m va_verify
```

### Command 1: Confirm Veteran Status (Simple)

This uses your `VA_API_KEY` and is the simplest check — just "yes, this person is a verified veteran" or "not confirmed."

```bash
python3 -m va_verify confirm \
  --first-name John \
  --last-name Doe \
  --dob 1980-01-15 \
  --address "123 Main St" \
  --city Austin \
  --state TX \
  --zip 78701 \
  --country USA
```

Replace the name, date of birth (`--dob`), and address with the real information for the veteran you are looking up.

### Command 2: Veteran Status (Detailed)

This uses your `VA_TOKEN` and gives slightly more detail, including a reason if someone is not confirmed.

```bash
python3 -m va_verify status \
  --first-name John \
  --last-name Doe \
  --dob 1980-01-15 \
  --address "123 Main St" \
  --city Austin \
  --state TX \
  --zip 78701 \
  --country USA
```

### Command 3: Service History

See all military service episodes — dates, branch, pay grade, and any deployments.

```bash
python3 -m va_verify service-history \
  --first-name John \
  --last-name Doe \
  --dob 1980-01-15 \
  --address "123 Main St" \
  --city Austin \
  --state TX \
  --zip 78701 \
  --country USA
```

### Command 4: Disability Rating

See the veteran's combined VA disability rating and the individual conditions that make it up.

```bash
python3 -m va_verify disability \
  --first-name John \
  --last-name Doe \
  --dob 1980-01-15 \
  --address "123 Main St" \
  --city Austin \
  --state TX \
  --zip 78701 \
  --country USA
```

### Command 5: Enrolled Benefits

See which VA benefit programs the veteran is currently enrolled in.

```bash
python3 -m va_verify benefits \
  --first-name John \
  --last-name Doe \
  --dob 1980-01-15 \
  --address "123 Main St" \
  --city Austin \
  --state TX \
  --zip 78701 \
  --country USA
```

### Command 6: Eligibility Flashes

"Flashes" are special eligibility markers — for example, whether someone qualifies under the PACT Act or was exposed to Agent Orange.

```bash
python3 -m va_verify flashes \
  --first-name John \
  --last-name Doe \
  --dob 1980-01-15 \
  --address "123 Main St" \
  --city Austin \
  --state TX \
  --zip 78701 \
  --country USA
```

---

## Understanding the Output

The program prints colorful results in your Terminal:

| Color | What It Means |
|-------|---------------|
| **Green** | Good news — confirmed, or high disability rating |
| **Yellow** | Partial or noteworthy — moderate disability rating |
| **Red** | Not confirmed, or something to pay attention to |

---

## Optional Extra Details

All commands accept these optional flags to help the VA match the right person:

| Flag | What It Is | Example |
|------|------------|---------|
| `--middle-name` | Middle name | `--middle-name Robert` |
| `--gender` | Gender (`M` or `F`) | `--gender M` |
| `--phone` | Phone number | `--phone 5125551234` |
| `--birth-place` | City and state of birth | `--birth-place "San Antonio TX"` |
| `--suffix` | Name suffix | `--suffix Jr` |

The more details you provide, the more likely the VA will find an exact match.

---

## Troubleshooting

### "command not found: python3"
Run `brew install python` again and then close and reopen your Terminal.

### "No module named va_verify"
Make sure you are in the `VA_API_Verify` folder. Type `pwd` to check your location. If needed, type `cd ~/Desktop/VA_API_Verify`.

### "401 Unauthorized" or "403 Forbidden"
Your API key or token is wrong or expired. Double-check your `.env` file (type `nano .env` to open it) and make sure the keys are correct with no extra spaces.

### "404 Not Found"
The veteran's information was not found in the VA system. Try adding more optional details (like `--middle-name` or `--gender`) to help narrow the search.

### "pip3: command not found"
Run `brew install python` to make sure Python and pip are installed together.

---

## Getting Help

- Type `python3 -m va_verify --help` to see all available commands.
- Type `python3 -m va_verify confirm --help` (or any command name) to see all options for that command.
- If something isn't working, ask a trusted adult or your organization's IT support.

---

## A Note About Privacy and Security

This tool connects to official U.S. Department of Veterans Affairs systems. Please:

- Only look up veterans with their **permission**, or as part of your **official job duties**.
- Keep your API keys **secret** — treat them like a password.
- Use the **sandbox** (test) environment while learning. Switch to `production` only when you have proper authorization.
- Never store veteran personal information beyond what is needed for your task.

> This project is for **authorized use only**. Misuse of VA APIs may violate federal law.

---

## Quick Reference Card

```
# See all commands
python3 -m va_verify --help

# Confirm veteran status (API Key)
python3 -m va_verify confirm --first-name FIRST --last-name LAST --dob YYYY-MM-DD --address "ADDR" --city CITY --state ST --zip ZIP --country USA

# Detailed veteran status (OAuth Token)
python3 -m va_verify status --first-name FIRST --last-name LAST --dob YYYY-MM-DD --address "ADDR" --city CITY --state ST --zip ZIP --country USA

# Service history
python3 -m va_verify service-history [same options as above]

# Disability rating
python3 -m va_verify disability [same options as above]

# Enrolled benefits
python3 -m va_verify benefits [same options as above]

# Eligibility flashes
python3 -m va_verify flashes [same options as above]
```
