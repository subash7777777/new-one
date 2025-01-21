# app.py
import streamlit as st
import pandas as pd
import numpy as np

def calculate_similarity_score(row, subject_property):
    """Calculate similarity score between a property and subject property."""
    market_value_diff = abs(row['Market Value-2024'] - subject_property['Market Value-2024']) / subject_property['Market Value-2024']
    vpr_diff = abs(row['VPR'] - subject_property['VPR']) / subject_property['VPR']
    # Weight market value difference more heavily (70%) than VPR difference (30%)
    return (market_value_diff * 0.7) + (vpr_diff * 0.3)

def find_comparables(df, subject_index):
    """Find comparable properties for given subject property."""
    subject_property = df.iloc[subject_index]
    
    # Create mask for each condition
    different_hotel = df['Hotel Name'] != subject_property['Hotel Name']
    different_address = df['Property Address'] != subject_property['Property Address']
    different_owner = df['Owner Name/ LLC Name'] != subject_property['Owner Name/ LLC Name']
    different_owner_address = df['Owner Street Address'] != subject_property['Owner Street Address']
    
    market_value_range = (abs(df['Market Value-2024'] - subject_property['Market Value-2024']) <= 100000)
    vpr_condition = df['VPR'] < subject_property['VPR'] * 0.5
    same_class = df['Hotel Class'] == subject_property['Hotel Class']
    is_hotel = df['Type'] == 'Hotel'
    
    # Exclude subject property
    not_subject = df.index != subject_index
    
    # Combine all conditions
    eligible_mask = (
        different_hotel &
        different_address &
        different_owner &
        different_owner_address &
        market_value_range &
        vpr_condition &
        same_class &
        is_hotel &
        not_subject
    )
    
    # Get eligible properties
    eligible_properties = df[eligible_mask].copy()
    
    if len(eligible_properties) == 0:
        return pd.DataFrame()
    
    # Calculate similarity scores
    eligible_properties['similarity_score'] = eligible_properties.apply(
        lambda row: calculate_similarity_score(row, subject_property), axis=1
    )
    
    # Sort by similarity score and get top 5
    comparable_properties = eligible_properties.nsmallest(5, 'similarity_score')
    return comparable_properties

def main():
    st.title("Hotel Property Comparables Generator")
    
    # File upload
    uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        # Load data
        df = pd.read_excel(uploaded_file)
        
        # Initialize session state for current index if not exists
        if 'current_index' not in st.session_state:
            st.session_state.current_index = 0
        
        # Navigation buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button('⬅️ Previous') and st.session_state.current_index > 0:
                st.session_state.current_index -= 1
        with col2:
            st.write(f"Property {st.session_state.current_index + 1} of {len(df)}")
        with col3:
            if st.button('Next ➡️') and st.session_state.current_index < len(df) - 1:
                st.session_state.current_index += 1
        
        # Get subject property and comparables
        subject_property = df.iloc[st.session_state.current_index:st.session_state.current_index+1]
        comparables = find_comparables(df, st.session_state.current_index)
        
        # Display results
        st.subheader("Subject Property")
        st.dataframe(subject_property)
        
        if len(comparables) > 0:
            st.subheader("Comparable Properties")
            st.dataframe(comparables.drop('similarity_score', axis=1))
            
            # Download results
            result_df = pd.concat([subject_property, comparables.drop('similarity_score', axis=1)])
            csv = result_df.to_csv(index=False)
            st.download_button(
                label="Download Current Results",
                data=csv,
                file_name=f"comparables_{st.session_state.current_index + 1}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No comparable properties found for the current subject property.")

if __name__ == "__main__":
    main()
