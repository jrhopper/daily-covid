#!/bin/env python3

from pprint import pprint
import os
from pathlib import Path
import sys
import argparse
from datetime import date
from .covid_plot import *
import subprocess
import requests


states = {"AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California",
    "CO":"Colorado","CT":"Connecticut","DE":"Delaware","FL":"Florida","GA":"Georgia",
    "HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas",
    "KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi",
    "MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey",
    "NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon",
    "PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah",
    "VT":"Vermont","VA":"Virginia","WA":"Washington","WV":"West Virginia",
    "WI":"Wisconsin","WY":"Wyoming"}



def createNewRow(row, previous):
    cases = f'{row[-2]}: delta={int(row[-2]) - int(previous[-2])}'
    deaths = f'{row[-1]}: delta={int(row[-1]) - int(previous[-1])}'
    return [dateFormat(row[0]), cases, deaths, row[1:]]

def shortenTable(rows):
    previous = rows[0]
    fixedFirstDay = [dateFormat(previous[0]), f'{previous[-2]} Δ={previous[-2]}', f'{previous[-1]} Δ={previous[-1]}']
    returnRows = [fixedFirstDay]

    for row in rows[1:]:
        newRow = createNewRow(row, previous)
        returnRows.append(newRow[0:-1])
        previous = newRow[-1]

    return returnRows

def csvCreate(rows, fname):
    with open(fname, 'w+', encoding='utf-8') as f:
        for i in rows:
            f.write(','.join(i))
            f.write('\n')

def updateReadme(nytDate):
    os.system('csvtomd All_Berkshire_Data_Provided.csv > markdown_table.md')
    print(f'Date NYT CSV: {latestDate}')
    print(f'Updating markdown_table.md and README.md for {latestDate}')
    os.system('cp README.md previous_README.md')
    updateReadme(dateFormat(rowsCols[-1][0]))
    print('README.md is up to date')

    with open('README.md', 'w+') as f:
        f.write(f'# Berkshire County, Massachusetts COVID-19 data\n\n')
        f.write(f'**Most Recent Update: {nytDate}**\n\n')
        f.write(f'This README is programatically updated and pushed from a VPS whenever a new days data is available.\n\n')
        f.write('[Using the New York Time\'s covid tracker](https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv)\n\n')
        f.write('`curl https://raw.githubusercontent.com/Fitzy1293/Berkshire-County-Covid/master/nytimes_covid.py`\n\n')
        f.write('`curl https://raw.githubusercontent.com/Fitzy1293/Berkshire-County-Covid/master/py`\n\n')
        f.write('`python3 nytimes_covid.py -state massachusetts -county berkshire -getdata`')
        f.write(f'![plots](COVID_plots.png)\n\n')
        f.write(f'# COVID daily data\n\n')

        f.write(''.join(open('markdown_table.md')))
        f.write('\n')

def nytimesUpdate(endpoint=''):
    print('Downloading NY times COVID-19 CSV\n')
    r = requests.get(endpoint)
    print('http status:', r.status_code)
    endpointTxt = r.text # Writing to disk and keeping in memory
    with open('us-counties.csv', 'w+') as f:
        f.write(r.text)

def run(**kwargs):
    if not os.path.exists(kwargs['countiesPath']):
        os.mkdir(kwargs['countiesPath'])

    endpoint = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"
    stateReplaceSpace = kwargs['state'].replace(' ', '_')
    countyReplaceSpace = kwargs['county'].replace(' ', '_')
    csvFname = f'{countyReplaceSpace}_{stateReplaceSpace}.csv'
    plotsFname = f'plots_{countyReplaceSpace}_{stateReplaceSpace}.png'

    csvPath = kwargs['countiesPath'] + csvFname
    plotsPath = kwargs['countiesPath'] + f'plots_{countyReplaceSpace}_{stateReplaceSpace}.png'

    rowsCols = [i.split(',') for i in kwargs['lines']]


    outputTable = [i for i in reversed(shortenTable(rowsCols))]
    head = ['Date', 'Cases (Total Δ=Daily Change)', 'Deaths (Total Δ=Daily Change)']
    csvData = [head] + outputTable
    csvCreate(csvData, csvPath)
    print(os.getcwd())
    print('output dir: counties')
    print(f'\tcsv: {csvFname}')
    print(f'\tplot: {plotsFname}')
    print()
    print('days:  ', len(rowsCols))
    print()
    print('\t'.join(rowsCols[-1]))
    print('\t'.join(rowsCols[0]))
    print('─' * 100)


    plotCovid(rowsCols, state=kwargs['state'], county=kwargs['county'], countiesPath=plotsPath)

    #if args.covidupdate:
    #     updateReadme(dateFormat(rowsCols[-1][0]))

def main():
    endpoint = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    parser = argparse.ArgumentParser(description='Create a tracker for COVID daily changes')
    parser.add_argument('-getdata',
                       action='store_true',
                       help=f'Download data from New York Times COVID endpoint\n{endpoint}')
    parser.add_argument('-state',
                       default=False,
                       help='U.S state')
    parser.add_argument('-county',
                       default=False,
                       help='County')
    parser.add_argument('-currentdata',
                       action='store_true',
                       help='Uses local us-counties.csv instead of downloading')
    parser.add_argument('-covidupdate',
                       action='store_true',
                       help='Update README\nNot ready')


    args = parser.parse_args()
    dictArgs = vars(args)

    counties = os.path.join(os.getcwd(),'counties','')


    if args.getdata: # Used when actually updating, shell online is easier
        nytimesUpdate(endpoint=endpoint)

    if args.state:
        if not os.path.exists('us-counties.csv'):
            nytimesUpdate(endpoint=endpoint)

        endpointTxt = open('us-counties.csv', 'r').read()

        state = states[dictArgs['state'].upper()].lower()

        if not args.county:
            counties = set([i.split(',')[1].lower() for i in endpointTxt.splitlines() if state.lower() == i.lower().split(',')[2]])
            counties = sorted(counties - {'unknown'})
        else:
            counties = [dictArgs['county'].lower()]
        pprint(counties)
        print()

        for county in counties:
            query = f',{county},{state},'
            countyStateStr = f'{state},{county}'
            fname = '_'.join(countyStateStr.lower().split(',')) + '.csv'

            stateCountyData = [i for i in endpointTxt.splitlines() if query.lower() in i.lower()]
            try:
                run(lines=stateCountyData,
                     state=state,
                     county=county,
                     countiesPath=os.path.join(os.getcwd(), 'counties', ''))
            except ZeroDivisionError:
                pass
