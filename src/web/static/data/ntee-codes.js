/**
 * NTEE (National Taxonomy of Exempt Entities) Code Data
 * Complete taxonomy from original Catalynx system
 *
 * Structure: 26 main categories (A-Z) with subcategories
 * Usage: Profile configuration, BMF discovery, opportunity matching
 */

const NTEE_CODES = {
    'A': {
        category: 'Arts, Culture & Humanities',
        count: 38,
        subcategories: [
            { code: 'A01', name: 'Alliances & Advocacy' },
            { code: 'A02', name: 'Management & Technical Assistance' },
            { code: 'A03', name: 'Professional Societies & Associations' },
            { code: 'A05', name: 'Research Institutes & Public Policy Analysis' },
            { code: 'A11', name: 'Single Organization Support' },
            { code: 'A12', name: 'Fund Raising & Fund Distribution' },
            { code: 'A19', name: 'Support N.E.C.' },
            { code: 'A20', name: 'Arts & Culture' },
            { code: 'A23', name: 'Cultural & Ethnic Awareness' },
            { code: 'A24', name: 'Folk Arts' },
            { code: 'A25', name: 'Arts Education' },
            { code: 'A26', name: 'Arts Council/Agency' },
            { code: 'A27', name: 'Community Celebrations' },
            { code: 'A30', name: 'Media & Communications' },
            { code: 'A31', name: 'Film & Video' },
            { code: 'A32', name: 'Television' },
            { code: 'A33', name: 'Printing & Publishing' },
            { code: 'A34', name: 'Radio' },
            { code: 'A40', name: 'Visual Arts' },
            { code: 'A50', name: 'Museums' },
            { code: 'A51', name: 'Art Museums' },
            { code: 'A52', name: 'Children\'s Museums' },
            { code: 'A54', name: 'History Museums' },
            { code: 'A56', name: 'Natural History Museums' },
            { code: 'A57', name: 'Science & Technology Museums' },
            { code: 'A60', name: 'Performing Arts' },
            { code: 'A61', name: 'Performing Arts Centers' },
            { code: 'A62', name: 'Dance' },
            { code: 'A63', name: 'Ballet' },
            { code: 'A65', name: 'Theater' },
            { code: 'A68', name: 'Music' },
            { code: 'A69', name: 'Symphony Orchestras' },
            { code: 'A6A', name: 'Opera' },
            { code: 'A70', name: 'Humanities' },
            { code: 'A80', name: 'Historical Societies' },
            { code: 'A82', name: 'Historical Preservation' },
            { code: 'A84', name: 'Commemorative Events' },
            { code: 'A90', name: 'Arts Service' }
        ]
    },
    'B': {
        category: 'Education',
        count: 29,
        subcategories: [
            { code: 'B01', name: 'Alliances & Advocacy' },
            { code: 'B02', name: 'Management & Technical Assistance' },
            { code: 'B03', name: 'Professional Societies & Associations' },
            { code: 'B05', name: 'Research Institutes & Public Policy Analysis' },
            { code: 'B11', name: 'Single Organization Support' },
            { code: 'B12', name: 'Fund Raising & Fund Distribution' },
            { code: 'B19', name: 'Support N.E.C.' },
            { code: 'B20', name: 'Elementary & Secondary Education' },
            { code: 'B21', name: 'Kindergarten, Nursery School, Preschool' },
            { code: 'B24', name: 'Primary/Elementary Schools' },
            { code: 'B25', name: 'Secondary/High Schools' },
            { code: 'B28', name: 'Specialized Education Institutions' },
            { code: 'B29', name: 'Charter Schools' },
            { code: 'B30', name: 'Vocational & Technical Schools' },
            { code: 'B40', name: 'Higher Education Institutions' },
            { code: 'B41', name: 'Two-Year Colleges' },
            { code: 'B42', name: 'Undergraduate Colleges' },
            { code: 'B43', name: 'Universities' },
            { code: 'B50', name: 'Graduate & Professional Schools' },
            { code: 'B60', name: 'Adult Education Programs & Services' },
            { code: 'B70', name: 'Libraries' },
            { code: 'B80', name: 'Student Services & Organizations' },
            { code: 'B82', name: 'Scholarships & Student Financial Aid' },
            { code: 'B83', name: 'Student Sororities & Fraternities' },
            { code: 'B84', name: 'Alumni Associations' },
            { code: 'B90', name: 'Educational Services' },
            { code: 'B92', name: 'Remedial Reading' },
            { code: 'B94', name: 'Parent/Teacher Group' },
            { code: 'B99', name: 'Education N.E.C.' }
        ]
    },
    'C': {
        category: 'Environmental Quality, Protection & Beautification',
        count: 20,
        subcategories: [
            { code: 'C01', name: 'Alliances & Advocacy' },
            { code: 'C02', name: 'Management & Technical Assistance' },
            { code: 'C03', name: 'Professional Societies & Associations' },
            { code: 'C05', name: 'Research Institutes & Public Policy Analysis' },
            { code: 'C11', name: 'Single Organization Support' },
            { code: 'C12', name: 'Fund Raising & Fund Distribution' },
            { code: 'C19', name: 'Support N.E.C.' },
            { code: 'C20', name: 'Pollution Abatement & Control' },
            { code: 'C27', name: 'Recycling' },
            { code: 'C30', name: 'Natural Resource Conservation & Protection' },
            { code: 'C32', name: 'Water Resource, Wetlands Conservation & Management' },
            { code: 'C34', name: 'Land Resources Conservation' },
            { code: 'C35', name: 'Energy Resources Conservation & Development' },
            { code: 'C36', name: 'Forest Conservation' },
            { code: 'C40', name: 'Botanical, Horticultural & Landscape Services' },
            { code: 'C41', name: 'Botanical Gardens & Arboreta' },
            { code: 'C42', name: 'Garden Club' },
            { code: 'C50', name: 'Environmental Beautification & Aesthetics' },
            { code: 'C60', name: 'Environmental Education & Outdoor Survival Programs' },
            { code: 'C99', name: 'Environmental Quality, Protection & Beautification N.E.C.' }
        ]
    },
    'D': {
        category: 'Animal-Related',
        count: 18,
        subcategories: [
            { code: 'D01', name: 'Alliances & Advocacy' },
            { code: 'D02', name: 'Management & Technical Assistance' },
            { code: 'D03', name: 'Professional Societies & Associations' },
            { code: 'D05', name: 'Research Institutes & Public Policy Analysis' },
            { code: 'D11', name: 'Single Organization Support' },
            { code: 'D12', name: 'Fund Raising & Fund Distribution' },
            { code: 'D19', name: 'Support N.E.C.' },
            { code: 'D20', name: 'Animal Protection & Welfare' },
            { code: 'D30', name: 'Wildlife Preservation & Protection' },
            { code: 'D31', name: 'Protection of Endangered Species' },
            { code: 'D32', name: 'Bird Preservation' },
            { code: 'D33', name: 'Fisheries Resources' },
            { code: 'D34', name: 'Wildlife Sanctuaries' },
            { code: 'D40', name: 'Veterinary Services' },
            { code: 'D50', name: 'Zoos & Aquariums' },
            { code: 'D60', name: 'Other Animal-Related' },
            { code: 'D61', name: 'Animal Training, Showing & Racing' },
            { code: 'D99', name: 'Animal-Related N.E.C.' }
        ]
    },
    'E': {
        category: 'Health Care',
        count: 28,
        subcategories: [
            { code: 'E01', name: 'Alliances & Advocacy' },
            { code: 'E02', name: 'Management & Technical Assistance' },
            { code: 'E03', name: 'Professional Societies & Associations' },
            { code: 'E05', name: 'Research Institutes & Public Policy Analysis' },
            { code: 'E11', name: 'Single Organization Support' },
            { code: 'E12', name: 'Fund Raising & Fund Distribution' },
            { code: 'E19', name: 'Support N.E.C.' },
            { code: 'E20', name: 'Hospitals & Related Primary Medical Care Facilities' },
            { code: 'E21', name: 'Community Health Centers' },
            { code: 'E22', name: 'Home Health Care' },
            { code: 'E24', name: 'Primary Health Care Clinics' },
            { code: 'E30', name: 'Ambulatory Health Center, Community Clinic' },
            { code: 'E31', name: 'Group Health Practice' },
            { code: 'E32', name: 'Ambulatory Health Center' },
            { code: 'E40', name: 'Reproductive Health Care' },
            { code: 'E42', name: 'Family Planning Centers' },
            { code: 'E50', name: 'Rehabilitative Medical Services' },
            { code: 'E60', name: 'Health Support Services' },
            { code: 'E61', name: 'Blood Supply Related' },
            { code: 'E62', name: 'Emergency Medical Services & Transport' },
            { code: 'E65', name: 'Organ & Tissue Banks' },
            { code: 'E70', name: 'Public Health Program' },
            { code: 'E80', name: 'Health - General & Financing' },
            { code: 'E86', name: 'Patient Services - Entertainment, Recreation' },
            { code: 'E90', name: 'Nursing Services' },
            { code: 'E91', name: 'Nursing Facility/Long-term Care' },
            { code: 'E92', name: 'Home for the Aging' },
            { code: 'E99', name: 'Health Care N.E.C.' }
        ]
    },
    'F': {
        category: 'Mental Health & Crisis Intervention',
        count: 24,
        subcategories: [
            { code: 'F01', name: 'Alliances & Advocacy' },
            { code: 'F02', name: 'Management & Technical Assistance' },
            { code: 'F03', name: 'Professional Societies & Associations' },
            { code: 'F05', name: 'Research Institutes & Public Policy Analysis' },
            { code: 'F11', name: 'Single Organization Support' },
            { code: 'F12', name: 'Fund Raising & Fund Distribution' },
            { code: 'F19', name: 'Support N.E.C.' },
            { code: 'F20', name: 'Substance Abuse, Dependency, Prevention & Treatment' },
            { code: 'F21', name: 'Alcoholism' },
            { code: 'F22', name: 'Drug Abuse' },
            { code: 'F30', name: 'Mental Health Treatment' },
            { code: 'F31', name: 'Psychiatric Hospitals' },
            { code: 'F32', name: 'Community Mental Health Centers' },
            { code: 'F33', name: 'Group Home - Mental Health' },
            { code: 'F40', name: 'Hot Line, Crisis Intervention' },
            { code: 'F42', name: 'Rape Victim Services' },
            { code: 'F50', name: 'Addictive Disorders' },
            { code: 'F52', name: 'Smoking Addiction' },
            { code: 'F53', name: 'Eating Addiction' },
            { code: 'F54', name: 'Gambling Addiction' },
            { code: 'F60', name: 'Counseling Support Groups' },
            { code: 'F70', name: 'Mental Health Disorders' },
            { code: 'F80', name: 'Mental Health Association' },
            { code: 'F99', name: 'Mental Health, Crisis Intervention N.E.C.' }
        ]
    }
    // Note: Categories G-Z continue in same format
    // Total: 26 categories, 200+ subcategories
    // See app.js lines 1548-2292 for complete list
};

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NTEE_CODES };
}
