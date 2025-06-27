import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle
import matplotlib.patheffects as path_effects

# Thiết lập figure
plt.figure(figsize=(14, 7))
plt.rcParams.update({'font.size': 11})
plt.rcParams.update({'font.family': 'DejaVu Sans'})

# Định nghĩa các vị trí
x_positions = [0.5, 3, 5.5, 8, 10.5]
box_width = 2
box_height = 4
arrow_length = 1

# Vẽ khung đầu vào
plt.gca().add_patch(Rectangle((x_positions[0]-box_width/2, 0), box_width, box_height, 
                              fill=True, alpha=0.1, ec='black', fc='lightblue'))
plt.text(x_positions[0], box_height+0.2, 'Tín hiệu đầu vào', ha='center', fontsize=12, fontweight='bold')

# Vẽ hình sóng rung động
x_wave = np.linspace(0, 1, 100)
y_wave1 = 0.3*np.sin(2*np.pi*5*x_wave) + 0.1*np.random.randn(100)
y_wave2 = 0.3*np.sin(2*np.pi*5*x_wave + np.pi/3) + 0.1*np.random.randn(100)
plt.plot(x_positions[0]-box_width/4 + x_wave*box_width/2, 3 + y_wave1, 'b-', lw=1)
plt.plot(x_positions[0]-box_width/4 + x_wave*box_width/2, 2 + y_wave2, 'b-', lw=1)

# Thêm chú thích cho tín hiệu đầu vào
plt.text(x_positions[0], 3.7, 'x(t) ∈ ℝ', ha='center', fontweight='bold')
plt.text(x_positions[0], 1, 'Tần số lấy mẫu: 20kHz', ha='center', fontsize=10)

# Vẽ phân cụm K-means
plt.scatter(x_positions[0]-0.5+np.random.rand(20)*0.8, 0.5+np.random.rand(20)*0.8, c='r', s=15, alpha=0.7)
plt.scatter(x_positions[0]-0.5+np.random.rand(20)*0.8, 0.5+np.random.rand(20)*0.8+0.8, c='b', s=15, alpha=0.7)
plt.scatter(x_positions[0]-0.5+np.random.rand(15)*0.8, 0.5+np.random.rand(15)*0.8+1.6, c='g', s=15, alpha=0.7)
plt.text(x_positions[0], 0.2, 'Phân cụm K-means', ha='center', fontsize=10)

# Vẽ khung trích xuất đặc trưng
plt.gca().add_patch(Rectangle((x_positions[1]-box_width/2, 1), box_width, box_height-1, 
                              fill=True, alpha=0.1, ec='black', fc='lightyellow'))
plt.text(x_positions[1], box_height+0.2, 'Trích xuất đặc trưng', ha='center', fontsize=12, fontweight='bold')

# Thêm công thức trích xuất đặc trưng
plt.text(x_positions[1], 3.5, 'f = [f₁, f₂, ..., f₄₆]', ha='center', fontweight='bold')
plt.text(x_positions[1], 3, 'f₁ = min(x)', ha='center', fontsize=9)
plt.text(x_positions[1], 2.7, 'f₂ = max(x)', ha='center', fontsize=9)
plt.text(x_positions[1], 2.4, 'f₃ = mean(x)', ha='center', fontsize=9)
plt.text(x_positions[1], 2.1, '...', ha='center', fontsize=9)
plt.text(x_positions[1], 1.8, 'f₄₆ = E_band(x)', ha='center', fontsize=9)

# Vẽ khung đặc trưng chính
plt.gca().add_patch(Rectangle((x_positions[2]-box_width/2, 1), box_width, box_height-1, 
                              fill=True, alpha=0.1, ec='black', fc='lightyellow'))
plt.text(x_positions[2], box_height+0.2, 'Các đặc trưng chính', ha='center', fontsize=12, fontweight='bold')

# Thêm công thức đặc trưng chính
plt.text(x_positions[2], 3.5, 'f\' = [f\'₁, f\'₂, ..., f\'₃₀]', ha='center', fontweight='bold')
plt.text(x_positions[2], 3, 'f\'₁ = selected(f₁)', ha='center', fontsize=9)
plt.text(x_positions[2], 2.7, 'f\'₂ = selected(f₂)', ha='center', fontsize=9)
plt.text(x_positions[2], 2.4, '...', ha='center', fontsize=9)
plt.text(x_positions[2], 2.1, 'f\'₃₀ = selected(f₄₆)', ha='center', fontsize=9)

# Vẽ khung mạng nơ-ron
plt.gca().add_patch(Rectangle((x_positions[3]-box_width/2, 0), box_width, box_height, 
                              fill=True, alpha=0.1, ec='black', fc='lightblue'))
plt.text(x_positions[3], box_height+0.2, 'Kiến trúc mạng', ha='center', fontsize=12, fontweight='bold')

# Vẽ mạng nơ-ron
# Input layer
input_neurons = 5
for i in range(input_neurons):
    circle = plt.Circle((x_positions[3]-0.8, 3.5-i*0.5), 0.15, fc='red', ec='black')
    plt.gca().add_patch(circle)

# Hidden layer
hidden_neurons = 3
for i in range(hidden_neurons):
    circle = plt.Circle((x_positions[3], 2.5-i*0.5), 0.15, fc='blue', ec='black')
    plt.gca().add_patch(circle)

# Output layer
output_neurons = 5
for i in range(output_neurons):
    circle = plt.Circle((x_positions[3]+0.8, 3.5-i*0.5), 0.15, fc='green', ec='black')
    plt.gca().add_patch(circle)

# Vẽ kết nối giữa các nơ-ron
for i in range(input_neurons):
    for j in range(hidden_neurons):
        plt.plot([x_positions[3]-0.8+0.15, x_positions[3]-0.15], 
                 [3.5-i*0.5, 2.5-j*0.5], 'k-', alpha=0.3, lw=0.5)

for i in range(hidden_neurons):
    for j in range(output_neurons):
        plt.plot([x_positions[3]+0.15, x_positions[3]+0.8-0.15], 
                 [2.5-i*0.5, 3.5-j*0.5], 'k-', alpha=0.3, lw=0.5)

# Thêm chú thích cho các lớp
plt.text(x_positions[3]-0.8, 1.2, 'Input layer', ha='center', fontsize=9)
plt.text(x_positions[3]-0.8, 0.9, 'X = f\' ∈ ℝ³⁰', ha='center', fontsize=9)

plt.text(x_positions[3], 1.2, 'Hidden layer', ha='center', fontsize=9)
plt.text(x_positions[3], 0.9, 'H = tanh(W₁X + b₁)', ha='center', fontsize=9)
plt.text(x_positions[3], 0.6, 'H ∈ ℝʰ, h ∈ [2,100]', ha='center', fontsize=9)

plt.text(x_positions[3]+0.8, 1.2, 'Output layer', ha='center', fontsize=9)
plt.text(x_positions[3]+0.8, 0.9, 'Y = softmax(W₂H + b₂)', ha='center', fontsize=9)
plt.text(x_positions[3]+0.8, 0.6, 'Y ∈ ℝ⁵', ha='center', fontsize=9)

# Vẽ khung kết quả
plt.gca().add_patch(Rectangle((x_positions[4]-box_width/2, 1), box_width, box_height-1, 
                              fill=True, alpha=0.1, ec='black', fc='lightgreen'))
plt.text(x_positions[4], box_height+0.2, 'Kết quả', ha='center', fontsize=12, fontweight='bold')

# Thêm các lớp phân loại
classes = ['early', 'normal', 'suspect', 'failure', 'stage 2']
for i, cls in enumerate(classes):
    plt.text(x_positions[4], 3.5-i*0.5, cls, ha='center', fontweight='bold')

# Vẽ các mũi tên kết nối
arrow_props = dict(arrowstyle='->', lw=1.5, color='black')
plt.annotate('', xy=(x_positions[1]-box_width/2, 2.5), xytext=(x_positions[0]+box_width/2, 2.5),
             arrowprops=arrow_props)
plt.annotate('', xy=(x_positions[2]-box_width/2, 2.5), xytext=(x_positions[1]+box_width/2, 2.5),
             arrowprops=arrow_props)
plt.annotate('', xy=(x_positions[3]-box_width/2, 2.5), xytext=(x_positions[2]+box_width/2, 2.5),
             arrowprops=arrow_props)
plt.annotate('', xy=(x_positions[4]-box_width/2, 2.5), xytext=(x_positions[3]+box_width/2, 2.5),
             arrowprops=arrow_props)

# Thêm công thức huấn luyện mô hình
plt.text(x_positions[3], 0.3, 'Huấn luyện: L = -∑ y_i log(ŷ_i) + α||W||²', ha='center', fontsize=9)
plt.text(x_positions[3], 0.1, 'Tối ưu: Adam với α ∈ {0.0001, 0.001, 0.01, 0.1}', ha='center', fontsize=9)

# Xóa các trục
plt.axis('off')
plt.tight_layout()

# Lưu hình
plt.savefig('mo_hinh_toan_hoc.png', dpi=300, bbox_inches='tight')
plt.close()

print("Đã tạo hình ảnh mo_hinh_toan_hoc.png thành công!") 