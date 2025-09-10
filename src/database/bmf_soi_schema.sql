-- BMF/SOI Comprehensive Database Schema
-- Nonprofit Financial Intelligence Platform
-- Created: September 10, 2025
--
-- This schema combines IRS Business Master File (BMF) data with
-- Statistics of Income (SOI) annual extract data for comprehensive
-- nonprofit financial intelligence across multiple form types and years.

-- =====================================================================================
-- MASTER BMF ORGANIZATIONS TABLE (Base Index)
-- =====================================================================================
-- Source: IRS Business Master File Extract (EO BMF)
-- Coverage: All tax-exempt organizations with EIN
-- Purpose: Master reference table with basic organizational data

CREATE TABLE IF NOT EXISTS bmf_organizations (
    -- Primary identification
    ein TEXT PRIMARY KEY,                    -- Employer Identification Number (unique)
    name TEXT NOT NULL,                     -- Organization name
    ico TEXT,                               -- In care of name
    
    -- Location information
    street TEXT,                            -- Street address
    city TEXT,                              -- City
    state TEXT,                             -- State abbreviation
    zip TEXT,                               -- ZIP code
    
    -- Classification and status
    ntee_code TEXT,                         -- National Taxonomy of Exempt Entities code
    subsection TEXT,                        -- Tax code subsection
    classification TEXT,                    -- Organization classification
    foundation_code TEXT,                   -- Foundation type code
    organization_code TEXT,                 -- Organization type code
    
    -- Financial summary (basic BMF data)
    asset_cd TEXT,                          -- Asset amount code
    income_cd TEXT,                         -- Income amount code  
    asset_amt INTEGER,                      -- Asset amount
    income_amt INTEGER,                     -- Income amount
    revenue_amt INTEGER,                    -- Revenue amount
    
    -- Administrative
    ruling_date TEXT,                       -- IRS ruling date
    tax_period TEXT,                        -- Tax period
    accounting_period TEXT,                 -- Accounting period
    sort_name TEXT,                         -- Alternate sort name
    
    -- Audit fields
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================================
-- FORM 990 TABLE (Large Nonprofits)
-- =====================================================================================
-- Source: IRS Annual Extract of Tax-Exempt Organization Financial Data (990)
-- Coverage: Organizations with gross receipts >= $200K or total assets >= $500K
-- Purpose: Detailed financial and operational data for larger nonprofits

CREATE TABLE IF NOT EXISTS form_990 (
    -- Primary keys and identification
    ein TEXT NOT NULL,                      -- Links to bmf_organizations
    tax_year INTEGER NOT NULL,              -- Tax year (2022, 2023, 2024)
    tax_pd INTEGER,                         -- Tax period (YYYYMM format)
    
    -- Filing information
    efile TEXT,                             -- E-file indicator (E/P)
    subseccd INTEGER,                       -- Subsection code
    
    -- Core financial data
    totrevenue INTEGER,                     -- Total revenue
    totcntrbgfts INTEGER,                   -- Total contributions, gifts, grants
    prgmservrevnue INTEGER,                 -- Program service revenue
    totfuncexpns INTEGER,                   -- Total functional expenses
    totassetsend INTEGER,                   -- Total assets end of year
    totliabend INTEGER,                     -- Total liabilities end of year
    totnetassetend INTEGER,                 -- Total net assets end of year
    
    -- Revenue breakdown
    invstmntinc INTEGER,                    -- Investment income
    txexmptbndsproceeds INTEGER,            -- Tax-exempt bond proceeds
    royaltsinc INTEGER,                     -- Royalties income
    grsrntsreal INTEGER,                    -- Gross rents - real estate
    grsrntsprsnl INTEGER,                   -- Gross rents - personal property
    netrntlinc INTEGER,                     -- Net rental income
    netgnls INTEGER,                        -- Net gains/losses from sales
    grsincfndrsng INTEGER,                  -- Gross income from fundraising
    netincfndrsng INTEGER,                  -- Net income from fundraising
    grsincgaming INTEGER,                   -- Gross income from gaming
    netincgaming INTEGER,                   -- Net income from gaming
    grsalesinvent INTEGER,                  -- Gross sales of inventory
    netincsales INTEGER,                    -- Net income from sales
    
    -- Program service revenue details (up to 6 categories)
    prgmservcode2acd TEXT,                  -- Program service code 2a
    totrev2acola INTEGER,                   -- Program service revenue 2a
    prgmservcode2bcd TEXT,                  -- Program service code 2b
    totrev2bcola INTEGER,                   -- Program service revenue 2b
    prgmservcode2ccd TEXT,                  -- Program service code 2c
    totrev2ccola INTEGER,                   -- Program service revenue 2c
    prgmservcode2dcd TEXT,                  -- Program service code 2d
    totrev2dcola INTEGER,                   -- Program service revenue 2d
    prgmservcode2ecd TEXT,                  -- Program service code 2e
    totrev2ecola INTEGER,                   -- Program service revenue 2e
    totrev2fcola INTEGER,                   -- Program service revenue other
    
    -- Expense breakdown
    grntstogovt INTEGER,                    -- Grants to government
    grnsttoindiv INTEGER,                   -- Grants to individuals
    grntstofrgngovt INTEGER,                -- Grants to foreign governments
    benifitsmembrs INTEGER,                 -- Benefits paid to members
    compnsatncurrofcr INTEGER,              -- Compensation of current officers
    compnsatnandothr INTEGER,               -- Compensation of other employees
    othrsalwages INTEGER,                   -- Other salaries and wages
    pensionplancontrb INTEGER,              -- Pension plan contributions
    othremplyeebenef INTEGER,               -- Other employee benefits
    payrolltx INTEGER,                      -- Payroll taxes
    feesforsrvcmgmt INTEGER,                -- Fees for services - management
    legalfees INTEGER,                      -- Legal fees
    accntingfees INTEGER,                   -- Accounting fees
    feesforsrvclobby INTEGER,               -- Fees for services - lobbying
    profndraising INTEGER,                  -- Professional fundraising fees
    feesforsrvcinvstmgmt INTEGER,           -- Fees for services - investment mgmt
    feesforsrvcothr INTEGER,                -- Fees for services - other
    advrtpromo INTEGER,                     -- Advertising and promotion
    officexpns INTEGER,                     -- Office expenses
    infotech INTEGER,                       -- Information technology
    royaltsexpns INTEGER,                   -- Royalties expenses
    occupancy INTEGER,                      -- Occupancy
    travel INTEGER,                         -- Travel
    travelofpublicoffcl INTEGER,            -- Travel of public officials
    converconventmtng INTEGER,              -- Conferences, conventions, meetings
    interestamt INTEGER,                    -- Interest
    pymtoaffiliates INTEGER,                -- Payments to affiliates
    deprcatndepletn INTEGER,                -- Depreciation, depletion
    insurance INTEGER,                      -- Insurance
    
    -- Other expenses (multiple categories)
    othrexpnsa INTEGER,                     -- Other expenses A
    othrexpnsb INTEGER,                     -- Other expenses B
    othrexpnsc INTEGER,                     -- Other expenses C
    othrexpnsd INTEGER,                     -- Other expenses D
    othrexpnse INTEGER,                     -- Other expenses E
    othrexpnsf INTEGER,                     -- Other expenses F
    
    -- Assets breakdown
    nonintcashend INTEGER,                  -- Cash non-interest-bearing EOY
    svngstempinvend INTEGER,                -- Savings and temporary investments EOY
    pldgegrntrcvblend INTEGER,              -- Pledges and grants receivable EOY
    accntsrcvblend INTEGER,                 -- Accounts receivable EOY
    currfrmrcvblend INTEGER,                -- Current frm officers, directors, etc EOY
    rcvbldisqualend INTEGER,                -- Receivable from disqualified persons EOY
    notesloansrcvblend INTEGER,             -- Notes and loans receivable EOY
    invntriesalesend INTEGER,               -- Inventories for sale EOY
    prepaidexpnsend INTEGER,                -- Prepaid expenses EOY
    lndbldgsequipend INTEGER,               -- Land, buildings, equipment EOY
    invstmntsend INTEGER,                   -- Investments - publicly traded EOY
    invstmntsothrend INTEGER,               -- Investments - other EOY
    invstmntsprgmend INTEGER,               -- Investments - program-related EOY
    intangibleassetsend INTEGER,            -- Intangible assets EOY
    othrassetsend INTEGER,                  -- Other assets EOY
    
    -- Liabilities breakdown
    accntspayableend INTEGER,               -- Accounts payable EOY
    grntspayableend INTEGER,                -- Grants payable EOY
    deferedrevnuend INTEGER,                -- Deferred revenue EOY
    txexmptbndsend INTEGER,                 -- Tax-exempt bonds EOY
    escrwaccntliabend INTEGER,              -- Escrow account liability EOY
    paybletoffcrsend INTEGER,               -- Payable to officers, directors, etc EOY
    secrdmrtgsend INTEGER,                  -- Secured mortgages EOY
    unsecurednotesend INTEGER,              -- Unsecured notes EOY
    othrliabend INTEGER,                    -- Other liabilities EOY
    
    -- Net assets breakdown
    unrstrctnetasstsend INTEGER,            -- Unrestricted net assets EOY
    temprstrctnetasstsend INTEGER,          -- Temporarily restricted net assets EOY
    permrstrctnetasstsend INTEGER,          -- Permanently restricted net assets EOY
    
    -- Compensation and governance
    totreprtabled INTEGER,                  -- Total reportable compensation
    totcomprelatede INTEGER,                -- Total compensation from related orgs
    totestcompf INTEGER,                    -- Total other compensation
    noindiv100kcnt INTEGER,                 -- Number individuals > $100K compensation
    nocontractor100kcnt INTEGER,            -- Number contractors > $100K
    
    -- Operational indicators (Y/N flags)
    s501c3or4947a1cd TEXT,                  -- 501(c)(3) or 4947(a)(1)?
    schdbind TEXT,                          -- Schedule B required?
    politicalactvtscd TEXT,                 -- Political activities?
    lbbyingactvtscd TEXT,                   -- Lobbying activities?
    operateschools170cd TEXT,               -- Operates schools?
    operatehosptlcd TEXT,                   -- Operates hospital?
    frgnofficecd TEXT,                      -- Foreign office?
    frgnrevexpnscd TEXT,                    -- Foreign activities?
    frgngrntscd TEXT,                       -- Foreign grants > $5K?
    rptgrntstogovtcd TEXT,                  -- Reports grants to government?
    rptgrntstoindvcd TEXT,                  -- Reports grants to individuals?
    rptprofndrsngfeescd TEXT,               -- Professional fundraising?
    rptincfnndrsngcd TEXT,                  -- Fundraising activities?
    rptincgamingcd TEXT,                    -- Gaming activities?
    txexmptbndcd TEXT,                      -- Tax-exempt bonds?
    dnradvisedfundscd TEXT,                 -- Donor advised funds?
    prptyintrcvdcd TEXT,                    -- Conservation easements?
    maintwrkofartcd TEXT,                   -- Collections of art?
    crcounselingqstncd TEXT,                -- Credit counseling?
    hldassetsintermpermcd TEXT,             -- Endowments?
    
    -- Public support and filing requirements
    nonpfrea TEXT,                          -- Not private foundation reason
    totnooforgscnt INTEGER,                 -- Total number of organizations
    totsupport INTEGER,                     -- Total support
    gftgrntsrcvd170 INTEGER,                -- Gifts grants received 170
    pubsuppsubtot170 INTEGER,               -- Public support subtotal 170
    totsupp170 INTEGER,                     -- Total support 170
    
    -- 509(a) support test
    totgftgrntrcvd509 INTEGER,              -- Total gifts grants received 509
    grsrcptsadmissn509 INTEGER,             -- Gross receipts admissions 509
    grsrcptsactivities509 INTEGER,          -- Gross receipts activities 509
    txrevnuelevied509 INTEGER,              -- Tax revenue levied 509
    srvcsval509 INTEGER,                    -- Services value 509
    pubsuppsubtot509 INTEGER,               -- Public support subtotal 509
    totsupp509 INTEGER,                     -- Total support 509
    
    -- Audit and filing information
    unrelbusinccd TEXT,                     -- Unrelated business income?
    filedf990tcd TEXT,                      -- Filed 990-T?
    frgnacctcd TEXT,                        -- Foreign accounts?
    prohibtdtxshltrcd TEXT,                 -- Prohibited tax shelter?
    prtynotifyorgcd TEXT,                   -- Party notification?
    filedf8886tcd TEXT,                     -- Filed 8886-T?
    solicitcntrbcd TEXT,                    -- Solicit contributions?
    exprstmntcd TEXT,                       -- Express statement?
    providegoodscd TEXT,                    -- Provide goods?
    notfydnrvalcd TEXT,                     -- Notify donor value?
    filedf8282cd TEXT,                      -- Filed 8282?
    f8282cnt INTEGER,                       -- Form 8282 count
    fndsrcvdcd TEXT,                        -- Funds received?
    premiumspaidcd TEXT,                    -- Premiums paid?
    filedf8899cd TEXT,                      -- Filed 8899?
    filedf1098ccd TEXT,                     -- Filed 1098-C?
    
    -- Audit fields
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    -- Primary key and foreign key
    PRIMARY KEY (ein, tax_year),
    FOREIGN KEY (ein) REFERENCES bmf_organizations(ein)
);

-- =====================================================================================
-- FORM 990-PF TABLE (Private Foundations)
-- =====================================================================================
-- Source: IRS Annual Extract of Tax-Exempt Organization Financial Data (990-PF)
-- Coverage: Private foundations filing Form 990-PF
-- Purpose: Foundation financial data including grant-making activities

CREATE TABLE IF NOT EXISTS form_990pf (
    -- Primary keys and identification
    ein TEXT NOT NULL,                      -- Links to bmf_organizations
    tax_year INTEGER NOT NULL,              -- Tax year (2022, 2023, 2024)
    tax_prd INTEGER,                        -- Tax period (YYYYMM format)
    
    -- Filing and status information
    elf TEXT,                               -- E-file indicator
    eostatus INTEGER,                       -- EO status code
    operatingcd TEXT,                       -- Operating foundation code
    subcd INTEGER,                          -- Subsection code
    
    -- Asset valuation
    fairmrktvalamt INTEGER,                 -- Fair market value of assets
    fairmrktvaleoy INTEGER,                 -- Fair market value EOY
    totassetsend INTEGER,                   -- Total assets EOY (book value)
    
    -- Revenue and income
    grscontrgifts INTEGER,                  -- Gross contributions received
    schedbind TEXT,                         -- Schedule B required?
    intrstrvnue INTEGER,                    -- Interest revenue
    dividndsamt INTEGER,                    -- Dividends amount
    grsrents INTEGER,                       -- Gross rents
    grsslspramt INTEGER,                    -- Gross sales price amount
    costsold INTEGER,                       -- Cost of goods sold
    grsprofitbus INTEGER,                   -- Gross profit business
    otherincamt INTEGER,                    -- Other income amount
    totrcptperbks INTEGER,                  -- Total receipts per books
    totrcptnetinc INTEGER,                  -- Total receipts net investment income
    trcptadjnetinc INTEGER,                 -- Total receipts adjusted net income
    
    -- Expenses
    compofficers INTEGER,                   -- Compensation of officers
    pensplemplbenf INTEGER,                 -- Pension plans, employee benefits
    legalfeesamt INTEGER,                   -- Legal fees amount
    accountingfees INTEGER,                 -- Accounting fees
    interestamt INTEGER,                    -- Interest amount
    depreciationamt INTEGER,                -- Depreciation amount
    occupancyamt INTEGER,                   -- Occupancy amount
    travlconfmtngs INTEGER,                 -- Travel, conferences, meetings
    printingpubl INTEGER,                   -- Printing and publications
    topradmnexpnsa INTEGER,                 -- Total operating/admin expenses (a)
    topradmnexpnsb INTEGER,                 -- Total operating/admin expenses (b)
    topradmnexpnsd INTEGER,                 -- Total operating/admin expenses (d)
    
    -- Grant making (KEY FOUNDATION DATA)
    contrpdpbks INTEGER,                    -- Contributions, gifts, grants paid
    totexpnspbks INTEGER,                   -- Total expenses per books
    totexpnsnetinc INTEGER,                 -- Total expenses net investment income
    totexpnsadjnet INTEGER,                 -- Total expenses adjusted net income
    totexpnsexempt INTEGER,                 -- Total expenses exempt purpose
    
    -- Investment portfolio
    invstgovtoblig INTEGER,                 -- Investments in govt obligations
    invstcorpstk INTEGER,                   -- Investments in corporate stock
    invstcorpbnd INTEGER,                   -- Investments in corporate bonds
    totinvstsec INTEGER,                    -- Total investments in securities
    mrtgloans INTEGER,                      -- Mortgage loans
    othrinvstend INTEGER,                   -- Other investments EOY
    
    -- Financial position
    othrcashamt INTEGER,                    -- Other cash amount
    othrassetseoy INTEGER,                  -- Other assets EOY
    mrtgnotespay INTEGER,                   -- Mortgage notes payable
    othrliabltseoy INTEGER,                 -- Other liabilities EOY
    totliabend INTEGER,                     -- Total liabilities EOY
    tfundnworth INTEGER,                    -- Total fund net worth
    
    -- Capital gains and investment income
    totexcapgnls INTEGER,                   -- Total capital gains/losses
    totexcapgn INTEGER,                     -- Total capital gains
    totexcapls INTEGER,                     -- Total capital losses
    netinvstinc INTEGER,                    -- Net investment income
    adjnetinc INTEGER,                      -- Adjusted net income
    
    -- Distribution requirements
    distribamt INTEGER,                     -- Distribution amount required
    undistribincyr INTEGER,                 -- Undistributed income current year
    
    -- Qualifying distributions by year
    qlfydistriba INTEGER,                   -- Qualifying distributions year A
    qlfydistribb INTEGER,                   -- Qualifying distributions year B
    qlfydistribc INTEGER,                   -- Qualifying distributions year C
    qlfydistribd INTEGER,                   -- Qualifying distributions year D
    qlfydistribtot INTEGER,                 -- Qualifying distributions total
    
    -- Asset values by year
    valassetscola INTEGER,                  -- Value of assets column A
    valassetscolb INTEGER,                  -- Value of assets column B
    valassetscolc INTEGER,                  -- Value of assets column C
    valassetscold INTEGER,                  -- Value of assets column D
    valassetstot INTEGER,                   -- Value of assets total
    
    -- Minimum investment return calculation
    cmpmininvstret INTEGER,                 -- Minimum investment return
    
    -- Support calculations
    totsuprtcola INTEGER,                   -- Total support column A
    totsuprtcolb INTEGER,                   -- Total support column B
    totsuprtcolc INTEGER,                   -- Total support column C
    totsuprtcold INTEGER,                   -- Total support column D
    totsuprttot INTEGER,                    -- Total support total
    
    -- Public support calculations
    pubsuprtcola INTEGER,                   -- Public support column A
    pubsuprtcolb INTEGER,                   -- Public support column B
    pubsuprtcolc INTEGER,                   -- Public support column C
    pubsuprtcold INTEGER,                   -- Public support column D
    pubsuprttot INTEGER,                    -- Public support total
    
    -- Investment income by year
    grsinvstinca INTEGER,                   -- Gross investment income A
    grsinvstincb INTEGER,                   -- Gross investment income B
    grsinvstincc INTEGER,                   -- Gross investment income C
    grsinvstincd INTEGER,                   -- Gross investment income D
    grsinvstinctot INTEGER,                 -- Gross investment income total
    
    -- Future grants and program services
    grntapprvfut INTEGER,                   -- Grants approved for future payment
    progsrvcacold INTEGER,                  -- Program service A (old)
    progsrvcacole INTEGER,                  -- Program service A (current)
    progsrvcbcold INTEGER,                  -- Program service B (old)
    progsrvcbcole INTEGER,                  -- Program service B (current)
    progsrvcccold INTEGER,                  -- Program service C (old)
    progsrvcccole INTEGER,                  -- Program service C (current)
    
    -- Taxes
    invstexcisetx INTEGER,                  -- Investment excise tax
    sect511tx INTEGER,                      -- Section 511 tax
    subtitleatx INTEGER,                    -- Subtitle A tax
    totaxpyr INTEGER,                       -- Total tax paid current year
    esttaxcr INTEGER,                       -- Estimated tax credit
    txwithldsrc INTEGER,                    -- Tax withheld at source
    txpaidf2758 INTEGER,                    -- Tax paid Form 2758
    erronbkupwthld INTEGER,                 -- Erroneous backup withholding
    estpnlty INTEGER,                       -- Estimated penalty
    taxdue INTEGER,                         -- Tax due
    overpay INTEGER,                        -- Overpayment
    
    -- Compliance and operational flags
    sec4940notxcd TEXT,                     -- Section 4940 no tax?
    sec4940redtxcd TEXT,                    -- Section 4940 reduced tax?
    filedf990tcd TEXT,                      -- Filed Form 990-T?
    contractncd TEXT,                       -- Contract?
    furnishcpycd TEXT,                      -- Furnish copy?
    claimstatcd TEXT,                       -- Claim status?
    cntrbtrstxyrcd TEXT,                    -- Contributor tax year?
    acqdrindrintcd TEXT,                    -- Acquired indirect interest?
    orgcmplypubcd TEXT,                     -- Org comply public?
    filedlf1041ind TEXT,                    -- Filed in lieu of 1041?
    propexchcd TEXT,                        -- Property exchange?
    brwlndmnycd TEXT,                       -- Borrow/lend money?
    furngoodscd TEXT,                       -- Furnish goods?
    paidcmpncd TEXT,                        -- Paid compensation?
    transfercd TEXT,                        -- Transfer?
    agremkpaycd TEXT,                       -- Agreement make payment?
    exceptactsind TEXT,                     -- Exception acts?
    prioractvcd TEXT,                       -- Prior activities?
    undistrinccd TEXT,                      -- Undistributed income?
    applyprovind TEXT,                      -- Apply provisions?
    dirindirintcd TEXT,                     -- Direct/indirect interest?
    excesshldcd TEXT,                       -- Excess holdings?
    invstjexmptcd TEXT,                     -- Investment jeopardize exempt?
    prevjexmptcd TEXT,                      -- Previously jeopardize exempt?
    propgndacd TEXT,                        -- Propaganda?
    ipubelectcd TEXT,                       -- Influence public election?
    grntindivcd TEXT,                       -- Grant to individual?
    nchrtygrntcd TEXT,                      -- Non-charity grant?
    nreligiouscd TEXT,                      -- Non-religious?
    excesstanind TEXT,                      -- Excess transaction?
    rfprsnlbnftind TEXT,                    -- Receive personal benefit?
    pyprsnlbnftind TEXT,                    -- Pay personal benefit?
    
    -- Activity codes and other details
    crelamt INTEGER,                        -- Credit amount
    infleg TEXT,                            -- Information legal
    actnotpr TEXT,                          -- Activities not reported
    chgnprvrptcd TEXT,                      -- Change prior report?
    membershpduesd INTEGER,                 -- Membership dues (old)
    membershpduese INTEGER,                 -- Membership dues (current)
    intonsvngsd INTEGER,                    -- Interest on savings (old)
    intonsvngse INTEGER,                    -- Interest on savings (current)
    dvdndsintd INTEGER,                     -- Dividends interest (old)
    dvdndsinte INTEGER,                     -- Dividends interest (current)
    
    -- Transaction indicators
    trnsfrcashcd TEXT,                      -- Transfer cash?
    trnsothasstscd TEXT,                    -- Transfer other assets?
    salesasstscd TEXT,                      -- Sale of assets?
    prchsasstscd TEXT,                      -- Purchase of assets?
    rentlsfacltscd TEXT,                    -- Rental of facilities?
    reimbrsmntscd TEXT,                     -- Reimbursements?
    loansguarcd TEXT,                       -- Loans or guarantees?
    perfservicescd TEXT,                    -- Performance of services?
    sharngasstscd TEXT,                     -- Sharing of assets?
    
    -- Asset utilization
    tfairmrktunuse INTEGER,                 -- Fair market value unused
    valncharitassets INTEGER,               -- Value non-charitable assets
    
    -- Audit fields
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    -- Primary key and foreign key
    PRIMARY KEY (ein, tax_year),
    FOREIGN KEY (ein) REFERENCES bmf_organizations(ein)
);

-- =====================================================================================
-- FORM 990-EZ TABLE (Smaller Nonprofits)
-- =====================================================================================
-- Source: IRS Annual Extract of Tax-Exempt Organization Financial Data (990-EZ)
-- Coverage: Organizations with gross receipts < $200K and total assets < $500K
-- Purpose: Simplified financial data for smaller nonprofits

CREATE TABLE IF NOT EXISTS form_990ez (
    -- Primary keys and identification
    ein TEXT NOT NULL,                      -- Links to bmf_organizations
    tax_year INTEGER NOT NULL,              -- Tax year (2022, 2023, 2024)
    taxpd INTEGER,                          -- Tax period (YYYYMM format)
    
    -- Filing information
    efile TEXT,                             -- E-file indicator
    subseccd INTEGER,                       -- Subsection code
    
    -- Core financial data (simplified)
    totrevnue INTEGER,                      -- Total revenue
    totcntrbs INTEGER,                      -- Total contributions
    prgmservrev INTEGER,                    -- Program service revenue
    duesassesmnts INTEGER,                  -- Membership dues and assessments
    othrinvstinc INTEGER,                   -- Other investment income
    grsamtsalesastothr INTEGER,             -- Gross amount sales assets other
    basisalesexpnsothr INTEGER,             -- Basis sales expenses other
    gnsaleofastothr INTEGER,                -- Gain/loss sale of assets other
    grsincgaming INTEGER,                   -- Gross income gaming
    grsrevnuefndrsng INTEGER,               -- Gross revenue fundraising events
    direxpns INTEGER,                       -- Direct expenses
    netincfndrsng INTEGER,                  -- Net income fundraising events
    grsalesminusret INTEGER,                -- Gross sales minus returns
    costgoodsold INTEGER,                   -- Cost of goods sold
    grsprft INTEGER,                        -- Gross profit
    othrevnue INTEGER,                      -- Other revenue
    
    -- Expenses
    totexpns INTEGER,                       -- Total expenses
    grntsandothrasstnc INTEGER,             -- Grants and other assistance
    benftspaidtomembers INTEGER,            -- Benefits paid to members
    salariesothrcompempl INTEGER,           -- Salaries other compensation employees
    profndraising INTEGER,                  -- Professional fundraising fees
    totfundrsngexpns INTEGER,               -- Total fundraising expenses
    othrexpnstot INTEGER,                   -- Other expenses total
    totexpnspbks INTEGER,                   -- Total expenses per books
    
    -- Net position
    totexcessyr INTEGER,                    -- Total excess or deficit current year
    othrchgsnetassetfnd INTEGER,            -- Other changes net assets/fund balances
    totnetassetsend INTEGER,                -- Total net assets EOY
    totnetassetsbod INTEGER,                -- Total net assets BOY
    
    -- Assets (simplified)
    casheoyamount INTEGER,                  -- Cash EOY amount
    svgstempcshequivend INTEGER,            -- Savings temp cash equivalent EOY
    accntsrcvblend INTEGER,                 -- Accounts receivable EOY
    grntsrcvblend INTEGER,                  -- Grants receivable EOY
    rcvblefrmoffcrsend INTEGER,             -- Receivable from officers EOY
    rcvblerltdprtsend INTEGER,              -- Receivable related parties EOY
    invntriesfrslend INTEGER,               -- Inventories for sale EOY
    prepaidexpnsend INTEGER,                -- Prepaid expenses EOY
    lndbldngsequipend INTEGER,              -- Land, buildings, equipment EOY
    invstmntsend INTEGER,                   -- Investments EOY
    othrassetsend INTEGER,                  -- Other assets EOY
    totassetsend INTEGER,                   -- Total assets EOY
    
    -- Liabilities (simplified)
    accntspyblend INTEGER,                  -- Accounts payable EOY
    grntspyblend INTEGER,                   -- Grants payable EOY
    defrdrevnueend INTEGER,                 -- Deferred revenue EOY
    lyblttoffcrsend INTEGER,                -- Liability to officers EOY
    lbltyrltdprtsend INTEGER,               -- Liability related parties EOY
    mortgnotespyblend INTEGER,              -- Mortgage notes payable EOY
    othrliabltend INTEGER,                  -- Other liabilities EOY
    totliabltend INTEGER,                   -- Total liabilities EOY
    
    -- Operational indicators
    unrelbusincd INTEGER,                   -- Unrelated business income
    initiationfee INTEGER,                  -- Initiation fees
    grspublicrcpts INTEGER,                 -- Gross public receipts
    
    -- Public support calculations (simplified)
    nonpfrea TEXT,                          -- Not private foundation reason
    gftgrntrcvd170 INTEGER,                 -- Gifts grants received 170
    txrevnuelevied170 INTEGER,              -- Tax revenue levied 170
    srvcsval170 INTEGER,                    -- Services value 170
    grsinc170 INTEGER,                      -- Gross income 170
    grsrcptsrelatd170 INTEGER,              -- Gross receipts related 170
    totgftgrntrcvd509 INTEGER,              -- Total gifts grants received 509
    grsrcptsadmiss509 INTEGER,              -- Gross receipts admissions 509
    txrevnuelevied509 INTEGER,              -- Tax revenue levied 509
    srvcsval509 INTEGER,                    -- Services value 509
    subtotsuppinc509 INTEGER,               -- Subtotal support income 509
    totsupp509 INTEGER,                     -- Total support 509
    
    -- Audit fields
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    -- Primary key and foreign key
    PRIMARY KEY (ein, tax_year),
    FOREIGN KEY (ein) REFERENCES bmf_organizations(ein)
);

-- =====================================================================================
-- PERFORMANCE INDEXES
-- =====================================================================================
-- Strategic indexes for optimal query performance across discovery workflows

-- BMF Organizations indexes (core discovery)
CREATE INDEX IF NOT EXISTS idx_bmf_ntee_state ON bmf_organizations(ntee_code, state);
CREATE INDEX IF NOT EXISTS idx_bmf_state_revenue ON bmf_organizations(state, revenue_amt);
CREATE INDEX IF NOT EXISTS idx_bmf_classification ON bmf_organizations(classification, foundation_code);

-- Form 990 indexes (large nonprofit analysis)
CREATE INDEX IF NOT EXISTS idx_990_revenue_year ON form_990(totrevenue, tax_year);
CREATE INDEX IF NOT EXISTS idx_990_grants_govt ON form_990(grntstogovt, tax_year);
CREATE INDEX IF NOT EXISTS idx_990_grants_indiv ON form_990(grnsttoindiv, tax_year);
CREATE INDEX IF NOT EXISTS idx_990_assets_year ON form_990(totassetsend, tax_year);
CREATE INDEX IF NOT EXISTS idx_990_compensation ON form_990(compnsatncurrofcr, tax_year);
CREATE INDEX IF NOT EXISTS idx_990_operational ON form_990(operateschools170cd, operatehosptlcd, tax_year);

-- Form 990-PF indexes (foundation intelligence)
CREATE INDEX IF NOT EXISTS idx_990pf_grants_paid ON form_990pf(contrpdpbks, tax_year);
CREATE INDEX IF NOT EXISTS idx_990pf_assets_fmv ON form_990pf(fairmrktvalamt, tax_year);
CREATE INDEX IF NOT EXISTS idx_990pf_netincome ON form_990pf(adjnetinc, tax_year);
CREATE INDEX IF NOT EXISTS idx_990pf_future_grants ON form_990pf(grntapprvfut, tax_year);
CREATE INDEX IF NOT EXISTS idx_990pf_distributions ON form_990pf(distribamt, tax_year);

-- Form 990-EZ indexes (smaller nonprofit coverage)
CREATE INDEX IF NOT EXISTS idx_990ez_revenue_year ON form_990ez(totrevnue, tax_year);
CREATE INDEX IF NOT EXISTS idx_990ez_assets_year ON form_990ez(totassetsend, tax_year);
CREATE INDEX IF NOT EXISTS idx_990ez_contributions ON form_990ez(totcntrbs, tax_year);

-- Multi-table relationship indexes
CREATE INDEX IF NOT EXISTS idx_990_ein_year ON form_990(ein, tax_year);
CREATE INDEX IF NOT EXISTS idx_990pf_ein_year ON form_990pf(ein, tax_year);
CREATE INDEX IF NOT EXISTS idx_990ez_ein_year ON form_990ez(ein, tax_year);

-- =====================================================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================================================

-- Comprehensive organization view combining BMF + latest financial data
CREATE VIEW IF NOT EXISTS v_organizations_current AS
SELECT 
    b.ein,
    b.name,
    b.ntee_code,
    b.state,
    b.city,
    b.classification,
    b.foundation_code,
    -- Latest financial data from any form type
    COALESCE(f990.totrevenue, f990ez.totrevnue, 0) as latest_revenue,
    COALESCE(f990.totassetsend, f990ez.totassetsend, 0) as latest_assets,
    COALESCE(f990.grntstogovt, 0) as grants_to_government,
    COALESCE(f990.grnsttoindiv, 0) as grants_to_individuals,
    COALESCE(f990pf.contrpdpbks, 0) as foundation_grants_paid,
    -- Latest year with data
    COALESCE(f990.tax_year, f990ez.tax_year, f990pf.tax_year) as latest_tax_year,
    -- Form type indicator
    CASE 
        WHEN f990.ein IS NOT NULL THEN '990'
        WHEN f990pf.ein IS NOT NULL THEN '990-PF'
        WHEN f990ez.ein IS NOT NULL THEN '990-EZ'
        ELSE 'BMF-Only'
    END as form_type
FROM bmf_organizations b
LEFT JOIN (
    SELECT ein, totrevenue, totassetsend, grntstogovt, grnsttoindiv, tax_year,
           ROW_NUMBER() OVER (PARTITION BY ein ORDER BY tax_year DESC) as rn
    FROM form_990
) f990 ON b.ein = f990.ein AND f990.rn = 1
LEFT JOIN (
    SELECT ein, contrpdpbks, tax_year,
           ROW_NUMBER() OVER (PARTITION BY ein ORDER BY tax_year DESC) as rn
    FROM form_990pf
) f990pf ON b.ein = f990pf.ein AND f990pf.rn = 1
LEFT JOIN (
    SELECT ein, totrevnue, totassetsend, tax_year,
           ROW_NUMBER() OVER (PARTITION BY ein ORDER BY tax_year DESC) as rn
    FROM form_990ez
) f990ez ON b.ein = f990ez.ein AND f990ez.rn = 1;

-- Foundation intelligence view for grant-making analysis
CREATE VIEW IF NOT EXISTS v_foundations_active AS
SELECT 
    b.ein,
    b.name,
    b.state,
    b.city,
    pf.contrpdpbks as grants_paid_latest,
    pf.fairmrktvalamt as assets_fmv,
    pf.grntapprvfut as future_grants_approved,
    pf.distribamt as required_distribution,
    pf.adjnetinc as adjusted_net_income,
    pf.tax_year,
    -- Grant capacity indicators
    CASE 
        WHEN pf.contrpdpbks > 1000000 THEN 'Major'
        WHEN pf.contrpdpbks > 100000 THEN 'Significant' 
        WHEN pf.contrpdpbks > 10000 THEN 'Moderate'
        ELSE 'Small'
    END as grant_capacity_tier
FROM bmf_organizations b
INNER JOIN (
    SELECT ein, contrpdpbks, fairmrktvalamt, grntapprvfut, distribamt, adjnetinc, tax_year,
           ROW_NUMBER() OVER (PARTITION BY ein ORDER BY tax_year DESC) as rn
    FROM form_990pf
    WHERE contrpdpbks > 0  -- Only foundations that actually make grants
) pf ON b.ein = pf.ein AND pf.rn = 1
WHERE b.foundation_code IS NOT NULL;

-- =====================================================================================
-- DATA QUALITY AND COMPLETENESS TRACKING
-- =====================================================================================

CREATE TABLE IF NOT EXISTS data_import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- 'BMF', '990', '990-PF', '990-EZ'
    tax_year INTEGER,
    records_processed INTEGER,
    records_success INTEGER,
    records_error INTEGER,
    processing_time_seconds REAL,
    notes TEXT
);

-- =====================================================================================
-- SUMMARY
-- =====================================================================================
-- This schema provides comprehensive nonprofit financial intelligence with:
-- 
-- 1. Master BMF index with all tax-exempt organizations
-- 2. Detailed 990 data for large nonprofits (190+ fields)
-- 3. Foundation-specific 990-PF data for grant intelligence (150+ fields)
-- 4. Simplified 990-EZ data for smaller organizations (50+ fields)
-- 5. Strategic indexes for high-performance discovery queries
-- 6. Views for common analysis patterns
-- 7. Data quality tracking and audit capabilities
--
-- Total capacity: ~2M organizations across 3 years of financial data
-- Expected database size: 6-8GB with full Northeast coverage
-- Query performance: Sub-second with proper indexing