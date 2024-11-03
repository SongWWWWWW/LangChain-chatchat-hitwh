
import pandas as pd
import matplotlib.pyplot as plt
import io

# Use the user uploaded file directly
uploaded_content = b'h,T\n1,20\n2,30\n3,25\n'  # example content, replace with actual file content

# Read the uploaded content
data = pd.read_csv(io.BytesIO(uploaded_content))

# Create a bar chart
plt.bar(data['h'], data['T'])
plt.xlabel('h')
plt.ylabel('T')
plt.title('Bar Chart of h vs T')
plt.show()
