"""Check which 990-PF CSV columns are missing from database"""

# CSV columns
csv_cols = ['ACCOUNTINGFEES', 'ACQDRINDRINTCD', 'ACTNOTPR', 'ADJNETINC', 'ADJNETINCCOLA', 'ADJNETINCCOLB', 'ADJNETINCCOLC', 'ADJNETINCCOLD', 'ADJNETINCTOT', 'AGREMKPAYCD', 'APPLYPROVIND', 'BRWLNDMNYCD', 'CHGNPRVRPTCD', 'CLAIMSTATCD', 'CMPMININVSTRET', 'CNTRBTRSTXYRCD', 'COMPOFFICERS', 'CONTRACTNCD', 'CONTRPDPBKS', 'COSTSOLD', 'CRELAMT', 'DEPRECIATIONAMT', 'DIRINDIRINTCD', 'DISTRIBAMT', 'DIVIDNDSAMT', 'DVDNDSINTD', 'DVDNDSINTE', 'EIN', 'ELF', 'ENDWMNTSCOLA', 'ENDWMNTSCOLB', 'ENDWMNTSCOLC', 'ENDWMNTSCOLD', 'ENDWMNTSTOT', 'EOSTATUS', 'ERRONBKUPWTHLD', 'ESTPNLTY', 'ESTTAXCR', 'EXCEPTACTSIND', 'EXCESSHLDCD', 'EXCESSRCPTS', 'EXCPTRANSIND', 'FAIRMRKTVALAMT', 'FAIRMRKTVALEOY', 'FILEDF990TCD', 'FILEDLF1041IND', 'FURNGOODSCD', 'FURNISHCPYCD', 'GRNTAPPRVFUT', 'GRNTINDIVCD', 'GRSCONTRGIFTS', 'GRSINVSTINCA', 'GRSINVSTINCB', 'GRSINVSTINCC', 'GRSINVSTINCD', 'GRSINVSTINCTOT', 'GRSPROFITBUS', 'GRSRENTS', 'GRSSLSPRAMT', 'INFLEG', 'INTERESTAMT', 'INTONSVNGSD', 'INTONSVNGSE', 'INTRSTRVNUE', 'INVSTCORPBND', 'INVSTCORPSTK', 'INVSTEXCISETX', 'INVSTGOVTOBLIG', 'INVSTJEXMPTCD', 'IPUBELECTCD', 'LEGALFEESAMT', 'LOANSGUARCD', 'MEMBERSHPDUESD', 'MEMBERSHPDUESE', 'MRTGLOANS', 'MRTGNOTESPAY', 'NCHRTYGRNTCD', 'NETINVSTINC', 'NRELIGIOUSCD', 'OCCUPANCYAMT', 'OPERATINGCD', 'ORGCMPLYPUBCD', 'OTHERINCAMT', 'OTHRASSETSEOY', 'OTHRCASHAMT', 'OTHRINVSTEND', 'OTHRLIABLTSEOY', 'OVERPAY', 'PAIDCMPNCD', 'PENSPLEMPLBENF', 'PERFSERVICESCD', 'PRCHSASSTSCD', 'PREVJEXMPTCD', 'PRINTINGPUBL', 'PRIORACTVCD', 'PROGSRVCACOLD', 'PROGSRVCACOLE', 'PROGSRVCBCOLD', 'PROGSRVCBCOLE', 'PROGSRVCCCOLD', 'PROGSRVCCCOLE', 'PROGSRVCDCOLD', 'PROGSRVCDCOLE', 'PROGSRVCECOLD', 'PROGSRVCECOLE', 'PROGSRVCFCOLD', 'PROGSRVCFCOLE', 'PROGSRVCGCOLD', 'PROGSRVCGCOLE', 'PROPEXCHCD', 'PROPGNDACD', 'PUBSUPRTCOLA', 'PUBSUPRTCOLB', 'PUBSUPRTCOLC', 'PUBSUPRTCOLD', 'PUBSUPRTTOT', 'PYPRSNLBNFTIND', 'QLFYASSETA', 'QLFYASSETB', 'QLFYASSETC', 'QLFYASSETD', 'QLFYASSETTOT', 'QLFYDISTRIBA', 'QLFYDISTRIBB', 'QLFYDISTRIBC', 'QLFYDISTRIBD', 'QLFYDISTRIBTOT', 'REIMBRSMNTSCD', 'RENTLSFACLTSCD', 'RFPRSNLBNFTIND', 'S4960_TX_PYMT_CD', 'SALESASSTSCD', 'SCHEDBIND', 'SEC4940NOTXCD', 'SEC4940REDTXCD', 'SECT511TX', 'SHARNGASSTSCD', 'SUBCD', 'SUBTITLEATX', 'TAXDUE', 'TAX_PRD', 'TAX_YR', 'TFAIRMRKTUNUSE', 'TFUNDNWORTH', 'TOPRADMNEXPNSA', 'TOPRADMNEXPNSB', 'TOPRADMNEXPNSD', 'TOTASSETSEND', 'TOTAXPYR', 'TOTEXCAPGN', 'TOTEXCAPGNLS', 'TOTEXCAPLS', 'TOTEXPNSADJNET', 'TOTEXPNSEXEMPT', 'TOTEXPNSNETINC', 'TOTEXPNSPBKS', 'TOTINVSTSEC', 'TOTLIABEND', 'TOTRCPTNETINC', 'TOTRCPTPERBKS', 'TOTSUPRTCOLA', 'TOTSUPRTCOLB', 'TOTSUPRTCOLC', 'TOTSUPRTCOLD', 'TOTSUPRTTOT', 'TRANSFERCD', 'TRAVLCONFMTNGS', 'TRCPTADJNETINC', 'TRNSFRCASHCD', 'TRNSOTHASSTSCD', 'TXPAIDF2758', 'TXWITHLDSRC', 'UNDISTRIBINCYR', 'UNDISTRINCCD', 'VALASSETSCOLA', 'VALASSETSCOLB', 'VALASSETSCOLC', 'VALASSETSCOLD', 'VALASSETSTOT', 'VALNCHARITASSETS']

# DB columns (excluding created_at, updated_at)
db_cols = ['accountingfees', 'acqdrindrintcd', 'actnotpr', 'adjnetinc', 'agremkpaycd', 'applyprovind', 'brwlndmnycd', 'chgnprvrptcd', 'claimstatcd', 'cmpmininvstret', 'cntrbtrstxyrcd', 'compofficers', 'contractncd', 'contrpdpbks', 'costsold', 'crelamt', 'depreciationamt', 'dirindirintcd', 'distribamt', 'dividndsamt', 'dvdndsintd', 'dvdndsinte', 'ein', 'elf', 'eostatus', 'erronbkupwthld', 'estpnlty', 'esttaxcr', 'exceptactsind', 'excesshldcd', 'excesstanind', 'fairmrktvalamt', 'fairmrktvaleoy', 'filedf990tcd', 'filedlf1041ind', 'furngoodscd', 'furnishcpycd', 'grntapprvfut', 'grntindivcd', 'grscontrgifts', 'grsinvstinca', 'grsinvstincb', 'grsinvstincc', 'grsinvstincd', 'grsinvstinctot', 'grsprofitbus', 'grsrents', 'grsslspramt', 'infleg', 'interestamt', 'intonsvngsd', 'intonsvngse', 'intrstrvnue', 'invstcorpbnd', 'invstcorpstk', 'invstexcisetx', 'invstgovtoblig', 'invstjexmptcd', 'ipubelectcd', 'legalfeesamt', 'loansguarcd', 'membershpduesd', 'membershpduese', 'mrtgloans', 'mrtgnotespay', 'nchrtygrntcd', 'netinvstinc', 'nreligiouscd', 'occupancyamt', 'operatingcd', 'orgcmplypubcd', 'otherincamt', 'othrassetseoy', 'othrcashamt', 'othrinvstend', 'othrliabltseoy', 'overpay', 'paidcmpncd', 'pensplemplbenf', 'perfservicescd', 'prchsasstscd', 'prevjexmptcd', 'printingpubl', 'prioractvcd', 'progsrvcacold', 'progsrvcacole', 'progsrvcbcold', 'progsrvcbcole', 'progsrvcccold', 'progsrvcccole', 'propexchcd', 'propgndacd', 'pubsuprtcola', 'pubsuprtcolb', 'pubsuprtcolc', 'pubsuprtcold', 'pubsuprttot', 'pyprsnlbnftind', 'qlfydistriba', 'qlfydistribb', 'qlfydistribc', 'qlfydistribd', 'qlfydistribtot', 'reimbrsmntscd', 'rentlsfacltscd', 'rfprsnlbnftind', 'salesasstscd', 'schedbind', 'sec4940notxcd', 'sec4940redtxcd', 'sect511tx', 'sharngasstscd', 'subcd', 'subtitleatx', 'tax_prd', 'tax_year', 'taxdue', 'tfairmrktunuse', 'tfundnworth', 'topradmnexpnsa', 'topradmnexpnsb', 'topradmnexpnsd', 'totassetsend', 'totaxpyr', 'totexcapgn', 'totexcapgnls', 'totexcapls', 'totexpnsadjnet', 'totexpnsexempt', 'totexpnsnetinc', 'totexpnspbks', 'totinvstsec', 'totliabend', 'totrcptnetinc', 'totrcptperbks', 'totsuprtcola', 'totsuprtcolb', 'totsuprtcolc', 'totsuprtcold', 'totsuprttot', 'transfercd', 'travlconfmtngs', 'trcptadjnetinc', 'trnsfrcashcd', 'trnsothasstscd', 'txpaidf2758', 'txwithldsrc', 'undistribincyr', 'undistrinccd', 'valassetscola', 'valassetscolb', 'valassetscolc', 'valassetscold', 'valassetstot', 'valncharitassets']

# Normalize to lowercase
csv_lower = set([c.lower() for c in csv_cols])
db_lower = set(db_cols)

# Find missing and extra
missing_from_db = csv_lower - db_lower
extra_in_db = db_lower - csv_lower

print(f"CSV has {len(csv_cols)} columns")
print(f"DB has {len(db_cols)} columns (excluding created_at/updated_at)")
print(f"\n{'='*80}")
print(f"MISSING FROM DATABASE ({len(missing_from_db)} columns):")
print(f"{'='*80}")

# Categorize missing columns
important_missing = []
for col in sorted(missing_from_db):
    upper_col = col.upper()

    # Identify critical missing columns
    if any(keyword in col for keyword in [
        'adjnetinc',  # Adjusted net income (multi-year)
        'endwmnt',     # Endowment data
        'qlfyasset',   # Qualifying assets
        'progsrvc',    # Program service revenue (d-g categories)
        'excessrcpts', # Excess receipts
        'excptrans',   # Excess transactions
        's4960',       # Section 4960 tax payment
    ]):
        important_missing.append(upper_col)
        print(f"  [!] {upper_col} (IMPORTANT - Foundation intelligence)")
    else:
        print(f"      {upper_col}")

print(f"\n{'='*80}")
print(f"EXTRA IN DATABASE ({len(extra_in_db)} columns - not in CSV):")
print(f"{'='*80}")
for col in sorted(extra_in_db):
    print(f"      {col.upper()}")

print(f"\n{'='*80}")
print(f"ANALYSIS SUMMARY:")
print(f"{'='*80}")
print(f"Total CSV columns: {len(csv_cols)}")
print(f"Total DB columns: {len(db_cols)}")
print(f"Missing important columns: {len(important_missing)}")
print(f"\nIMPORTANT MISSING COLUMNS FOR FOUNDATION ANALYSIS:")
for col in important_missing:
    print(f"  - {col}")

if important_missing:
    print(f"\n[!] RECOMMENDATION: Add {len(important_missing)} important columns to database schema")
    print(f"These columns provide critical foundation grant-making intelligence.")
else:
    print(f"\n[OK] All important foundation intelligence columns are captured!")
