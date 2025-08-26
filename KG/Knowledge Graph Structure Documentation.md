# Knowledge Graph Structure Documentation

This document outlines the updated structure of the Knowledge Graph generated from the insurance Excel data, incorporating additional data from "Description_garanties.xlsx" and "Données_Assurance_S1.2_S2.xlsx". It details the various node labels, their properties, and the relationships connecting them. New additions include the `Garantie` node and associated relationships to represent guarantees offered by products and included in contracts, along with their descriptions and assured capitals.





## Node Labels and Properties

### PersonneMorale
- `ref_personne`: Unique identifier for the moral person (integer).
- `raison_sociale`: Company name (string).
- `matricule_fiscale`: Fiscal ID (string).
- `lib_secteur_activite`: Sector of activity (string).
- `lib_activite`: Activity (string).
- `ville`: City (string).
- `lib_gouvernorat`: Governorate (string).
- `ville_gouvernorat`: Governorate city (string).

### PersonnePhysique
- `ref_personne`: Unique identifier for the physical person (integer).
- `nom_prenom`: Full name (string).
- `date_naissance`: Date of birth (date string YYYY-MM-DD).
- `lieu_naissance`: Place of birth (string).
- `code_sexe`: Gender code (string).
- `situation_familiale`: Marital status (string).
- `num_piece_identite`: ID number (integer).
- `lib_secteur_activite`: Sector of activity (string).
- `lib_profession`: Profession (string).
- `ville`: City (string).
- `lib_gouvernorat`: Governorate (string).
- `ville_gouvernorat`: Governorate city (string).

### Contrat
- `num_contrat`: Contract number (integer).
- `lib_produit`: Product name (string).
- `effet_contrat`: Contract effective date (date string YYYY-MM-DD).
- `date_expiration`: Contract expiration date (date string YYYY-MM-DD).
- `prochain_terme`: Next term (string).
- `lib_etat_contrat`: Contract status (string).
- `branche`: Branch (string).
- `somme_quittances`: Sum of receipts (float).
- `statut_paiement`: Payment status (string).
- `capital_assure`: Insured capital (float).

### Sinistre
- `num_sinistre`: Claim number (integer).
- `lib_branche`: Branch (string).
- `lib_sous_branche`: Sub-branch (string).
- `lib_produit`: Product name (string).
- `nature_sinistre`: Nature of claim (string).
- `lib_type_sinistre`: Type of claim (string).
- `taux_responsabilite`: Responsibility rate (float).
- `date_survenance`: Date of occurrence (date string YYYY-MM-DD).
- `date_declaration`: Date of declaration (date string YYYY-MM-DD).
- `date_ouverture`: Date of opening (date string YYYY-MM-DD).
- `observation_sinistre`: Claim observation (string).
- `lib_etat_sinistre`: Claim status (string).
- `lieu_accident`: Accident location (string).
- `motif_reouverture`: Reopening reason (string).
- `montant_encaisse`: Amount collected (float).
- `montant_a_encaisser`: Amount to be collected (float).

### Branche
- `lib_branche`: Branch name (string).

### SousBranche
- `lib_sous_branche`: Sub-branch name (string).

### Produit
- `lib_produit`: Product name (string).

### Garantie
- `code_garantie`: Unique code for the guarantee (integer).
- `lib_garantie`: Guarantee name (string).
- `description`: Description of the guarantee (string).




## Relationships

- `[:A_SOUSCRIT]`: Connects `PersonneMorale` or `PersonnePhysique` nodes to `Contrat` nodes, indicating that a person has subscribed to a contract.
- `[:CONCERNE]`: Connects `Sinistre` nodes to `Contrat` nodes, indicating that a claim concerns a specific contract.
- `[:EST_UNE_SOUS_BRANCHE_DE]`: Connects `SousBranche` nodes to `Branche` nodes, indicating a hierarchical relationship where a sub-branch belongs to a branch.
- `[:EST_UN_PRODUIT_DE]`: Connects `Produit` nodes to `SousBranche` nodes, indicating that a product belongs to a sub-branch.
- `[:PORTE_SUR]`: Connects `Contrat` nodes to `Produit` nodes, indicating that a contract is for a specific product.
- `[:DE_BRANCHE]`: Connects `Contrat` or `Sinistre` nodes to `Branche` nodes, indicating the branch of the contract or claim.
- `[:DE_SOUS_BRANCHE]`: Connects `Sinistre` nodes to `SousBranche` nodes, indicating the sub-branch of the claim.
- `[:OFFRE]`: Connects `Produit` nodes to `Garantie` nodes, indicating that a product offers a specific guarantee.
- `[:INCLUT]`: Connects `Contrat` nodes to `Garantie` nodes, indicating that a contract includes a specific guarantee.  
  - Properties: `capital_assure` (float) - The insured capital amount for this guarantee in the contract.