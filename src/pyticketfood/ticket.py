import datetime as dt
from dataclasses import dataclass
from typing import List, Tuple, Optional
from pathlib import Path
import bs4
import requests


@dataclass
class Transaction:
    """Class for keeping track of an item in inventory."""
    date: dt.datetime
    value: float
    description: str





def parse_balance(html_content: str) -> Optional[float]:
    # Create a BeautifulSoup object to parse the HTML
    soup = bs4.BeautifulSoup(html_content, 'html.parser')
    
    # Find all <label> elements with class "valueLabel"
    value_labels = soup.find_all('label', class_='valueLabel')
    
    if len(value_labels) >= 2:
        # Extract the text content of the second <label> element
        account_balance = value_labels[1].get_text()
        return account_balance.strip()  # Remove leading/trailing whitespace
    
    # Return None if there are not enough "valueLabel" elements
    return None


def parse_single_transaction(el: bs4.element.Tag) -> Transaction:
    labels = el.find_all('label')
    assert len(labels) == 4

    # if value of label no. 3 is -, then expense, else income
    # value has format "131,61 €"
    # € needs to be removes, and ',' -> '.' before parsing flaot
    if labels[2].text == '-': # expense
        value = -float(labels[3].text[:-1].replace(',', '.'))
    else: # income
        value = float(labels[2].text[:-1].replace(',', '.'))

    return Transaction(
        date=dt.datetime.strptime(labels[0].text, "%Y-%m-%d"),
        value=value,
        description=labels[1].text
    )


def parse_transactions(text: str) -> List[Transaction]:
    soup = bs4.BeautifulSoup(text, 'html.parser')
    lst=soup.find_all(class_="row table-content")
    return [parse_single_transaction(l) for l in lst]


def get_transactions(username: str, password: str, start_date: dt.datetime, end_date:dt.datetime) -> Tuple[float, List[Transaction]]:
    with requests.Session() as session:
        # login
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            # 'Cookie': 'ASP.NET_SessionId=chv0olcmzqojke2gz0zyuwdc',
            'Origin': 'https://hbcartaoticket.unicre.pt',
            'Referer': 'https://hbcartaoticket.unicre.pt/?messageType=logout',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not)A;Brand";v="24", "Chromium";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }

        data = {
            'User': username,
            'Password': password,
        }
        r = session.post('https://hbcartaoticket.unicre.pt/', headers=headers, data=data)
        balance = parse_balance(r.text)
            

        headers = {
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            # 'Cookie': 'ASP.NET_SessionId=chv0olcmzqojke2gz0zyuwdc',
            'Referer': 'https://hbcartaoticket.unicre.pt/transacoes',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not)A;Brand";v="24", "Chromium";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }

        params = {
            'dateFrom': start_date.strftime("%Y-%m-%d"),
            'dateTo': end_date.strftime("%Y-%m-%d"),
        }

        r3 = session.get(
            'https://hbcartaoticket.unicre.pt/HomePrivate/PartialTransactionsList',
            params=params,
            headers=headers,
        )

        return balance, parse_transactions(r3.text)


    

def main():
    import os
    cred_vars = ['TICKET_USER', 'TICKET_PASS']
    credentials = []
    for v_name in cred_vars:
        if v_name not in os.environ:
            v_val = input(f'insert {v_name}:')
        else:
            v_val = os.environ[v_name]
        credentials.append(v_val)
        
    balance, T = get_transactions(credentials[0], credentials[1],
                                  dt.date(2022, 1, 1),
                                  dt.date.today()) # get new transactions, or init database if no db exists yet
    # from now on, I can just call the update method to get **new** transactions
    print(sorted(T, key=lambda x: x.date)) # sort by date
    print(f"current balnace is {balance}")


if __name__ == '__main__':
    main()