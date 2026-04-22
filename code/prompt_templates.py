"""
NFR Assistant - Prompt Templates
=================================
Structured prompts for different menu actions
"""

MENU_PROMPTS = {
    "define_entity": """
What is {user_input}?
Given this NFR type information:
{context}
State what type of entity it is in requirements engineering. Provide a clear and concise explanation of what {user_input} is and why it matters. Make it so that even people who have no expert knowledge in the requirements engineering field can understand. Provide easy to understand examples.
""",


    "browse_entity": """
Explain {user_input} based on this given this information about its decomposition methods and correlation rules:

{context}

Be concise but cover all information given to you. Do not change or add any offsprings in decomposition methods.
""",

   

    "decompose": """
An NFR softgoal can be decomposed into sub-softgoals. A decomposition helps define a softgoal, since it provides the components that makes up of the main softgoal.
Decompose the {user_input} NFR softgoal given the decomposition information:{context}. If there's no information, come up with the most plausible decomposition""",

    
    "show_examples": """
Try to explain in detail about what {user_input} is, given the information:

{context}

Provide a concise explanation covering all the information given but not in a way that is too verbose; provide an example. Be brief but helpful.
""",

    "show_operationalizations": """
Operationalizations are possible design alternatives for meeting or satisficing non-functional requirements in the system. Here is the operationalization information from the metamodel: {context}.
List and explain all operationalizations for the {user_input} softgoal. If there are no information from the metamodel, come up with possible operationalizations

""",


    "analyze_contributions": """



Every operationalization in the system can simultaneously have negative and positive effects on different non-functional requirements. 
Therefore, using one operationalization can help satisfice one NFR while hindering another. Here's the information about the {user_input} operationalization and their contribution for NFRs in the metamodel: {context} 
List each NFR the {user_input} operationalization affects, whether negatively or positively; analyze and list {user_input}'s trade-offs between NFRs.

""",

    "default": """
User query: {user_input}

Metamodel data:
{context}

Provide a helpful response based on this metamodel information. Be clear, practical, and grounded in the provided context.
""",

    
}